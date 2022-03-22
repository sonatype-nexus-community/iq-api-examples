import requests
import json
from urllib.parse import urlencode

# update IQ server location, username, and password
iq_url = "http://localhost:8070"
username = "admin"
password = "admin123"

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

components = [
	{"packageUrl" : "pkg:npm/node-ipc@10.*"},
	{"packageUrl" : "pkg:npm/node-ipc@11.*"},
	{"packageUrl" : "pkg:npm/node-ipc@9.1.*"}
]

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

print(output)
print("--------------------------------------")
with open("results.json", "w+") as file:
	file.write(output)
	print("Json results saved to -> results.json")

print("--------------------------------------")

