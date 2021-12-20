#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Python Dependencies
import json
import argparse
import asyncio
import aiohttp
import datetime

# ----------------------------------------------------------------------------
iq_url, iq_session, components, history, days = "", "", {}, {}, 0
today = datetime.datetime.now()
week_ago = today - datetime.timedelta(days=7)

def get_arguments():
    global iq_url, iq_session, iq_auth, days
    parser = argparse.ArgumentParser(description='List applications that have not scanned for a given number of days.')
    parser.add_argument('-u', '--url', help='', default="http://localhost:8070", required=False)
    parser.add_argument('-a', '--auth', help='', default="admin:admin123", required=False)
    parser.add_argument('-d', '--days', help='', default=5, required=False)
    args = vars(parser.parse_args())
    iq_url = args["url"]
    days = args['days']
    creds = args["auth"].split(":")
    iq_session = aiohttp.ClientSession()
    iq_auth = aiohttp.BasicAuth(creds[0], creds[1])
    return args

# ----------------------------------------------------------------------------
async def main():
    args = get_arguments()
    apps = await get_apps()
    stale = []
    for app_history in asyncio.as_completed([handle_history(app) for app in apps]):
        history.update(await app_history)

    for appId, app in history.items():
        if len(app['last_ci']):
            scan = app['last_ci']
            if scan['age'] >= days:
                tmp = app.copy()
                del tmp["reports"]
                tmp.update({'applicationId': appId})
                stale.append(tmp)

    if len(stale):
        print(f'{len(stale)} app(s) not scanned in the last {days} days.')
    else:
        print(f'All apps scanned in the last {days} days.')

    save_results("results.json", stale, True)
    await iq_session.close()

# ----------------------------------------------------------------------------
async def get_apps():
    url = f'{iq_url}/api/v2/applications'
    apps = await get_url(url, "applications")
    if apps is None: 
        print('No apps found')
        await iq_session.close()
        exit(1)
    return apps

async def handle_history(app):
	resp, appId = {}, app['id']
	url = f'{iq_url}/api/v2/reports/applications/{appId}/history'
	app_history = await get_url(url)
	app['last_ci'] = {}
	for report in app_history['reports']:
		scan_date = c_eval(report['evaluationDate'])
		report['age'] = (today - scan_date).days
		clean_dict(report,['applicationId','latestReportHtmlUrl',
			'reportHtmlUrl','embeddableReportHtmlUrl','reportPdfUrl',
			'reportDataUrl','policyEvaluationResult'])

	for report in app_history['reports']:
		if not report['isForMonitoring']:
			app['last_ci'] = report
			break

	app.update(app_history)
	clean_dict(app,['id','contactUserName','applicationTags','applicationId'])
	resp = {appId: app}
	return resp

# ----------------------------------------------------------------------------
def pp(page):
    print(json.dumps(page, indent=4))

def clean_dict(dictionary, remove_list):
    for e in remove_list: 
        dictionary.pop(e, None)

def save_results(file_name, results, indent=False):
    with open(file_name, "w+") as file:
        if indent:
              file.write(json.dumps(results, indent=4))
        else: file.write(json.dumps(results))
    print(f"Json results saved to -> {file_name}")

def c_eval(dt):
    return datetime.datetime.fromisoformat(dt).replace(tzinfo=None)

def short(dd):
    return dd.strftime("%Y-%m-%d")

async def get_url(url, root=""):
    resp = await iq_session.get(url, auth=iq_auth)
    if resp.status != 200: return None
    node = await resp.json()
    if root in node: node = node[root]
    if node is None or len(node) == 0: return None
    return node
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------  
if __name__ == "__main__":
    asyncio.run(main())
    