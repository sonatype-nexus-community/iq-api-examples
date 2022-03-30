import requests
import argparse
import json
from urllib.parse import urlencode

def __parse_args():
    parser = argparse.ArgumentParser(
        description='Connects to IQ and finds all applications with referenced components.')
    parser.add_argument('-s', dest='iq_url', default='http://localhost:8070', help='URL of IQ instance.', required=False)
    parser.add_argument('-u', dest='username', default='admin', required=False)
    parser.add_argument('-p', dest='password', default='admin123', required=False)
    parser.add_argument('-i',  dest='input_file', default='packageUrl.txt', help='text file of packageUrls', required=False)
    return parser.parse_args()

args = __parse_args()
iq_url = args.iq_url
username = args.username
password = args.password
iq_session = requests.Session()
iq_session.auth = requests.auth.HTTPBasicAuth(username, password)
stages = ["build","stage-release","release","operate"]
results = []

print("--------------------------------------")

## test for IQ server
try:
	url = f"{iq_url}/api/v2/applications"
	response = iq_session.get(url)
	response.raise_for_status()

except (iq_session.exceptions.ConnectionError, iq_session.exceptions.Timeout):
	print("Cannot find IQ Server, check URL")
	exit()

except iq_session.exceptions.HTTPError:
	print("Could not authenticate, check username and password")
	exit()

url = f"{iq_url}/rest/product/version"
response = iq_session.get(url)
version = response.json()['version']
print(f'IQ Server Version {version}')


components = []
with open("packageUrl.txt", "r") as f:
	for packageUrl in f:
		components.append({"packageUrl":packageUrl.strip()})

for component in components:
	for stage in stages:
		component['stageId'] = stage
		params = urlencode(component).replace("%27", "%22")
		url = f"{iq_url}/api/v2/search/component?{params}"
		response = iq_session.get(url)

		for result in response.json()['results']:
			# to reduce noise in results
			del result["componentIdentifier"]
			result['stage'] = stage
			results.append(result)

output = json.dumps(results, indent=4)

print("--------------------------------------")
with open("results.json", "w+") as file:
	file.write(output)
	print("Json results saved to -> results.json")

print("--------------------------------------")

for result in results:
	ll = [result["applicationId"], result["stage"], result["packageUrl"]]
	print(ll)

