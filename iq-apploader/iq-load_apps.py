import os
import csv
import argparse
import subprocess
import json

from requests import Session
from requests.auth import HTTPBasicAuth

iq_session = Session()

def main():
	parser = argparse.ArgumentParser(description='Add and scan applications in the basepath folder.  Uses auto applications feature for id that are not already present.')
	parser.add_argument('-a','--auth', default="admin:admin", required=False)
	parser.add_argument('-u','--url', default="http://localhost:8070", required=False)
	parser.add_argument('-b','--basepath', default="apps/", required=False)
	parser.add_argument('-f','--file_name', default="export.csv", required=False)
	a = vars(parser.parse_args())
	auth, iq_url, basepath, file_name = a["auth"], a["url"], a["basepath"], a["file_name"]
	iq_session.auth = HTTPBasicAuth(auth.split(":")[0], auth.split(":")[1] )
	#----------------------------------------------------------------------

	# Step 1. Check that Auto application creation is turned on and turn it on if needed.
	autoApplications( iq_url )

	# Step 2. Look into basepath folder and build a list of applications to scan.
	exportFilesCSV( basepath, file_name )

	# Step 3. Working through scan list; update temp file of finished scans/exitcodes/links.
	scanAppsCSV( file_name, iq_url, auth )

	#----------------------------------------------------------------------
#--------------------------------------------------------------------------
def exportFilesCSV(basepath, file_name):
	extensions = [".jar",".war",".ear",".zip",".tar",".tar.bz2",".tar.gz",
		".tgz",".bz2",".tbz2",".nupkg",".dll",".js",".whl",".egg",".rpm"]
	apps, head = [], ['publicId', 'extension', 'path','status','link']
	for r, d, z in os.walk(basepath):
		for n in z:
			s, p = os.path.splitext(n), os.path.join(r, n)
			if s[1] in extensions:
				apps.append({
					"publicId": s[0].replace(" ", "_"),
					"extension": s[1], "path":p, "status":"", "link":""})
	with open(file_name, mode='w') as f:
		w = csv.DictWriter(f, fieldnames=head)
		w.writeheader()
		for a in apps:
			w.writerow(a)
	return apps

def scanAppsCSV(file_name, iq_url, auth):
	cli = get_IQ_CLI_Version( iq_url )
	with open(file_name, mode='r+') as file, open("temp_"+file_name, 'w') as temp:
		c, apps = 0, csv.DictReader(file)
		results = csv.DictWriter(temp, fieldnames=apps.fieldnames)
		results.writeheader()
		for app in apps:
			print("Starting scan: '{}'".format(app["publicId"]))
			cmd = ["java", "-jar", cli, "-s", iq_url, "-a", auth, "-i", app["publicId"], app["path"]]
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
		#print(f"Processed {c} applications.")

def get_IQ_CLI_Version(iq_url):
	url = '{}/rest/user-telemetry/config'.format( iq_url )
	response = iq_session.get(url).json()
	iq_version = response["account"]["iq-server-version"]
	print("IQ Server Version {}".format(iq_version))
	cli = "nexus-iq-cli-{}.jar".format(iq_version)
	if not os.path.isfile(cli):
		print("Downloading CLI: {}".format(cli))
		url = "https://download.sonatype.com/clm/scanner/{}".format(cli)
		r = Session().get(url)
		with open(cli, 'wb') as f:
			f.write(r.content)
	return cli

def autoApplications(iq_url):
	iq_session.cookies.set('CLM-CSRF-TOKEN', 'api')
	iq_headers = {'X-CSRF-TOKEN': 'api'}
	url = '{}/rest/config/automaticApplications'.format(iq_url)
	print (url)
	response = iq_session.get(url).json()
	if not response["enabled"]:
		print ("Auto-applications is required to onboarding with this script.")
		data = {'enabled': True, 'parentOrganizationId': response["parentOrganizationId"]}
		iq_session.put( url , json=data, headers=iq_headers)

def searchingApps():
	url = '{}/api/v2/applications'.format(args["url"])
	response = iq_session.get(url).json()
	for app in response["applications"]:
		if args["appId"] in [app["name"], app["id"], app["publicId"]]:
			appId.append(app["id"])

#--------------------------------------------------------------------
if __name__ == "__main__":
	main()
