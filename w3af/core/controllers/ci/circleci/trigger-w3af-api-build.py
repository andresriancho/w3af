#!/usr/bin/env python

import os
import json
import requests


if __name__ == '__main__':
    headers = {'Content-Type': 'application/json'}

    url = ('https://circleci.com/api/v1/project/andresriancho/'
           'w3af-api-docker/tree/%s?circle-token=%s')
    branch = os.environ.get('CIRCLE_BRANCH')
    token = os.environ.get('W3AF_API_DOCKER_TOKEN')

    latest_w3af_tag = file('/tmp/new-w3af-docker-tag.txt').read()

    data = {'build_parameters': {'W3AF_REGISTRY_TAG': latest_w3af_tag}}
    data = json.dumps(data)
    requests.post(url % (branch, token), headers=headers, data=data)

