# Copyright (c) 2011-present Sonatype, Inc. All rights reserved.
# "Sonatype" is a trademark of Sonatype, Inc.

import argparse
import csv
import json
import requests


LICENSE_OVERRIDE_ENDPOINT = '/rest/licenseOverride/organization/ROOT_ORGANIZATION_ID'
LOGIN_ENDPOINT = '/rest/user/session'


http_headers = {'Content-Type':'application/json;charset=UTF-8', 'Accept':'application/json, text/plain, */*'}


def __post_login(server_url, endpoint, username, password):
    # Need to login to get a valid CSRF token.
    session = requests.Session()
    session.auth = (username, password)
    response = session.post(server_url+endpoint, headers=http_headers)
    http_headers['X-CSRF-TOKEN'] = response.cookies['CLM-CSRF-TOKEN']
    if response.status_code != 204:
        raise ConnectionError(response.reason)
    return session


def __post_license_override(server_url, endpoint, session, json_data):
    response = session.post(server_url + endpoint,json=json_data, headers=http_headers)
    if response.status_code != 200:
        raise ConnectionError(response.reason)


def __parse_input_file(input_file, read_first_row):
    # Constructs the JSON for the post body from the rows in the TSV file.
    with open(input_file, newline='', encoding='utf-8') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t', quoting=csv.QUOTE_MINIMAL)

        if  not read_first_row:
            next(reader)

        results = []
        for row in reader:
            override_json = {}
            override_json['componentIdentifier'] = json.loads(row[0])
            override_json['licenseIds'] = [x.replace(' ','') for x in row[1].split(',')]

            if row[2]:
                override_json['comment'] = row[2]

            override_json['status'] = 'OVERRIDDEN'
            override_json['ownerId'] = 'ROOT_ORGANIZATION_ID'

            results.append(override_json)

        return results


def __override_licenses(server_url, session, license_overrides):
    for license_override in license_overrides:
        __post_license_override(server_url, LICENSE_OVERRIDE_ENDPOINT, session, license_override)


def __parse_args():
    parser = argparse.ArgumentParser(
        description='Connects to IQ and uses the provided TSV file to override component licenses.')
    parser.add_argument('-s', dest='server_url',
                        default='http://localhost:8070', help='URL of IQ instance.', required=True)
    parser.add_argument('-u', dest='username', help='IQ user\'s username.', required=True)
    parser.add_argument('-p', dest='password', help='IQ user\'s password.', required=True)
    parser.add_argument('-i',  dest='input_file',
                        default='input.tsv', help='A TSV file that contains the component identifier, its license, and an optional comment.', required=True)
    parser.add_argument('-r', dest='read_first_row',
                        default=False, help='Optional argument to read the first row; the input TSV file is assumed to have a header row by default.', action='store_true')

    return parser.parse_args()


if __name__ == "__main__":
    args = __parse_args()
    session = __post_login(args.server_url, LOGIN_ENDPOINT, args.username, args.password)
    license_overrides = __parse_input_file(args.input_file, args.read_first_row)
    __override_licenses(args.server_url, session, license_overrides)