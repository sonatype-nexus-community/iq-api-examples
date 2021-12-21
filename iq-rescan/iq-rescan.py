import requests
import json
import time
import datetime
import argparse

iq_url, iq_session, interval, skip = "", {}, 100, []
today = datetime.datetime.now()

def get_arguments():
	global iq_url, iq_session, interval, skip
	parser = argparse.ArgumentParser(description='List applications that have not scanned for a given number of days.')
	parser.add_argument('-u', '--url', help='', default="http://localhost:8070", required=False)
	parser.add_argument('-a', '--auth', help='', default="admin:admin123", required=False)
	parser.add_argument('-d', '--interval', help='', default=7, required=False)
	parser.add_argument('-s', '--skip', help='', default="develop:operate", required=False)
	args = vars(parser.parse_args())
	iq_url = args["url"]
	interval = int(args['interval'])
	creds = args["auth"].split(":")
	skip = args["skip"].split(":")
	iq_session = requests.Session()
	iq_session.auth = requests.auth.HTTPBasicAuth(creds[0], creds[1])
	return args
#-------------------------------------------------------------
args = get_arguments()
print('-'*60)
print(f'Starting rescan for reports older than {interval} days.')
# Find all applications
url = f'{iq_url}/api/v2/applications'
apps =  iq_session.get(url).json()['applications']

for app in apps:
	publicId = app['publicId']
	name = app['name']
	appId = app['id']

	print('\n'+'-'*40+'\n'+f"Reviewing: '{name}' - '{publicId}'")
	# Get application reports
	url = f"{iq_url}/api/v2/reports/applications/{appId}"
	reports = iq_session.get(url).json()
	#----------------------------------
	for report in reports:
		stage = report['stage']
		dt = report['evaluationDate']
		days = (today - datetime.datetime.fromisoformat(dt.replace('Z', '')).replace(tzinfo=None)).days
		print(f"Stage : '{stage}'' was scanned {days} days ago.")
		if days < interval or stage in skip: print('-- skipping'); continue
		#----------------------------------
		print('rescanning...')	
		# Promoting last scan for stage to the same stage.
		data = {"sourceStageId": stage,"targetStageId": stage}
		url = f"{iq_url}/api/v2/evaluation/applications/{appId}/promoteScan"
		resp = iq_session.post(url, json=data)
		#----------------------------------
		url = f"{iq_url}/{resp.json()['statusUrl']}"
		status = 'PENDING'; ii = 0
		# Waiting for results.
		while status == 'PENDING' and ii < 60:
			time.sleep(2); ii += 2
			if (ii % 10) == 0: print(status)
			resp = iq_session.get(url).json()
			status = resp['status']
		print(status)

print('\n'+'-'*60+'\n --- end --- \n'+'-'*60)
#-----------------------------------------------------