import os
import csv
import argparse
import subprocess
import json
import requests

iq_url, iq_auth, basepath, file_name, creds, iq_version, iq_cli = "", "", "", "", ['',''], "", ""
iq_session = requests.Session()
iq_headers = {'X-CSRF-TOKEN': 'api'}
iq_session.cookies.set('CLM-CSRF-TOKEN', 'api')

extensions = [
	".jar",".war",".ear",".zip",
	".tar",".tar.bz2",".tar.gz",
	".tgz",".bz2",".tbz2",".nupkg",
	".dll",".js",".whl",".egg",".rpm"
]

def get_arguments():
	parser = argparse.ArgumentParser(description='Add and scan applications in the basepath folder.  Uses auto applications feature for id that are not already present.')
	parser.add_argument('-a','--auth', default="admin:admin123", required=False)
	parser.add_argument('-u','--url', default="http://localhost:8070", required=False)
	parser.add_argument('-b','--basepath', default="apps/", required=False)
	parser.add_argument('-f','--file_name', default="export.csv", required=False)
	return vars(parser.parse_args())

def main():
	global iq_url, basepath, file_name, creds, iq_version, iq_cli, iq_auth
	args = get_arguments()
	iq_url = args["url"] 
	basepath = args["basepath"]
	file_name = args["file_name"]
	iq_auth = args["auth"]
	creds = iq_auth.split(":")
	iq_session.auth = requests.auth.HTTPBasicAuth(creds[0], creds[1]) 
	#----------------------------------------------------------------------
	iq_version = get_iq_version()
	iq_cli = f'nexus-iq-cli-{iq_version}.jar'
	get_cli()

	# Test auto-application creation
	test_auto_applications()
	
	if os.path.isfile(file_name):
		print('Found csv file')
	else:
		apps = get_apps()
		export_csv(apps)

	# Step 3. Working through scan list; update temp file of finished scans/exitcodes/links.
	scanAppsCSV()

	#----------------------------------------------------------------------
#--------------------------------------------------------------------------

def test_auto_applications():
	url = f"{iq_url}/rest/config/automaticApplications"
	resp = iq_session.get(url).json()
	if not resp["enabled"]:
		print('Auto Applications is not configured.  Please turn it on before continuing.')
		exit()

def get_apps():
	apps= []
	print(f'Looking for applications in "{basepath}"')
	for root, dirs, files in os.walk(basepath):
		for name in files:
			print(f"-- found: {name}")
			filenames = os.path.splitext(name)
			publicId = filenames[0].replace(" ", "_")
			extension = filenames[1]
			paths = os.path.join(root, name)
			app = {"publicId": publicId, "extension": extension, 
					"path": paths, "status": "", "link": ""}
			if extension in extensions:
				apps.append(app)
	print(f"Found {len(apps)} apps")
	return apps

def export_csv(apps):
	if len(apps) > 0:	
		head = list(apps[0].keys())
		with open(file_name, mode='w') as file:
			writer = csv.DictWriter(file, fieldnames=head)
			writer.writeheader()
			for app in apps:
				writer.writerow(app)

def scanAppsCSV():
	with open(file_name, mode='r+') as file, open("temp_"+file_name, 'w') as temp:
		c, apps = 0, csv.DictReader(file)
		results = csv.DictWriter(temp, fieldnames=apps.fieldnames)
		results.writeheader()
		for app in apps:
			publicId, path, report_url = app['publicId'], app["path"], ""
			print("-"*80)
			print(f"Starting scan: {publicId}")
			print("-"*80)
			cmd = ["java", "-jar", iq_cli, "-s", iq_url, "-a", iq_auth, "-i", publicId, path]
			process = subprocess.Popen(cmd, bufsize=1, universal_newlines=True, 
					stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			for line in iter(process.stdout.readline, ''):
				if "detailed report" in line:
					report_url = line[ line.find("http"):-1]
				print (line[:-1])
			process.wait()
			app["status"] = process.returncode
			app["link"] = report_url
			results.writerow(app)
			c+=1
			#if c ==1: break
		print(f'Processed {c} applications.')

def get_iq_version():
	url = f'{iq_url}/rest/user-telemetry/config'
	resp = iq_session.get(url).json()
	return resp["account"]["iq-server-version"]

def get_cli():
	if not os.path.isfile(iq_cli):
		print(f'Downloading CLI: {iq_cli}')
		url = f'https://download.sonatype.com/clm/scanner/{iq_cli}'
		resp = requests.Session().get(url)
		with open(iq_cli, 'wb') as file:
			file.write(resp.content)	

def pp(page):
    print(json.dumps(page, indent=4))

#--------------------------------------------------------------------
if __name__ == "__main__":
	main()
