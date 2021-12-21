import requests
import json
import time
import datetime

iq_session = requests.Session()
iq_session.auth = requests.auth.HTTPBasicAuth("admin", "admin123")
iq_url = "http://localhost:8070"
today = datetime.datetime.now()
interval = 7
#-------------------------------------------------------------
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
		days = (today - datetime.datetime.fromisoformat(dt).replace(tzinfo=None)).days
		print(f"Stage : '{stage}'' was scanned {days} days ago.")
		if days < interval: print('-- skipping'); continue
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