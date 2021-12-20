import os
import csv
import argparse
import subprocess
import json
import requests

iq_url, iq_auth, iq_session, iq_headers = "", "", "", ""
extensions = [
	".jar",".war",".ear",".zip",
	".tar",".tar.bz2",".tar.gz",
	".tgz",".bz2",".tbz2",".nupkg",
	".dll",".js",".whl",".egg",".rpm"
]

def main():
	global iq_url, iq_session, iq_auth, iq_headers
	parser = argparse.ArgumentParser(description='Add and scan applications in the basepath folder.  Uses auto applications feature for id that are not already present.')
	parser.add_argument('-a','--auth', default="admin:admin123", required=False)
	parser.add_argument('-u','--url', default="http://localhost:8070", required=False)
	parser.add_argument('-b','--basepath', default="apps/", required=False)
	parser.add_argument('-f','--file_name', default="export.csv", required=False)
	args = vars(parser.parse_args())
	iq_url, basepath, file_name = args["url"], args["basepath"], args["file_name"]
	iq_session = requests.Session()
	iq_auth = args["auth"] 
    creds = iq_auth.split(":")
	iq_headers = {'X-CSRF-TOKEN': 'api'}
	iq_session.cookies.set('CLM-CSRF-TOKEN', 'api')
    iq_session.auth = requests.auth.HTTPBasicAuth(creds[0], creds[1]) 
	#----------------------------------------------------------------------
	
	# Turn on auto-application creation if needed
	auto_applications()

	apps = get_apps(args["basepath"])
	export_csv(apps, file_name)

	# Step 3. Working through scan list; update temp file of finished scans/exitcodes/links.
	scanAppsCSV(file_name)

	#----------------------------------------------------------------------
#--------------------------------------------------------------------------

def auto_applications():
	resp = iq_session.get(f'{iq_url}/rest/config/automaticApplications').json()
	po = resp["parentOrganizationId"]
	if not resp["enabled"]:
		data = {'enabled': True, 'parentOrganizationId': po}
		iq_session.put( url , json=data, headers=iq_headers)

def get_apps(basepath):
	apps= []
	for root, dirs, files in os.walk(basepath):
		for name in files:
			filenames = os.path.splitext(name)
			publicId = filenames[0].replace(" ", "_")
			extension = filenames[1]
			paths = os.path.join(root, name)
			app = {"publicId": publicId, "extension": extension, 
					"path": paths, "status": "", "link": ""}

			if extension in extensions:
				apps.append(app)
	return apps

def export_csv(apps, file_name):
	if len(apps) > 0:	
		head = list(apps[0].keys())
		with open(file_name, mode='w') as file:
			writer = csv.DictWriter(file, fieldnames=head)
			writer.writeheader()
			for app in apps:
				writer.writerow(app)

def scanAppsCSV(file_name):
	cli = get_cli()

	with open(file_name, mode='r+') as file, open("temp_"+file_name, 'w') as temp:
		c, apps = 0, csv.DictReader(file)
		results = csv.DictWriter(temp, fieldnames=apps.fieldnames)
		results.writeheader()
		for app in apps:
			publicId, path = app['publicId'], app["path"]
			print(f"Starting scan: {publicId}")

			cmd = ["java", "-jar", cli, "-s", iq_url, "-a", iq_auth, "-i", publicId, path]
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

def get_cli():
	iq_version = get_iq_version()
	print(f'IQ Server Version {iq_version}')
	cli = f'nexus-iq-cli-{iq_version}.jar'
	download_cli(cli)
	return cli

def download_cli(cli):
	if not os.path.isfile(cli):
		print(f'Downloading CLI: {cli}')
		url = f'https://download.sonatype.com/clm/scanner/{cli}'
		resp = requests.Session().get(url)
		with open(cli, 'wb') as file:
			file.write(resp.content)	

def get_iq_version():
	url = f'{iq_url}/rest/user-telemetry/config'
	resp = iq_session.get(url).json()
	return resp["account"]["iq-server-version"]

#--------------------------------------------------------------------
if __name__ == "__main__":
	main()
