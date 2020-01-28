#!/usr/bin/env python

# This program is used to create an Ansible dynamic inventory source for use
# with Ansible Tower 2.8.1 which runs python 2.7.  The inventory is sourced
# from an Arista Cloud Vision (CVP) server.  The following Environment
# variables are required:
#
#   CVP_SERVER: the URL to the CVP server
#   CVP_USER: the login user-name
#   CVP_PASSWORD: the login password
#
# The output of this program is the Ansible inventory in JSON as described in
# their documentation online:
# https://docs.ansible.com/ansible/2.8/dev_guide/developing_inventory.html#developing-inventory

import sys
import os
import json
import requests
from collections import defaultdict


class CvpSession(requests.Session):
    def __init__(self):
        try:
            server = os.environ['CVP_SERVER']
            username = os.environ['CVP_USER']
            password = os.environ['CVP_PASSWORD']
        except KeyError as exc:
            sys.exit("Missing required enviornment variable: {var}".format(var=exc.args[0]))

        super(CvpSession, self).__init__()
        self.host_url = "https://{server}/web".format(server=server)
        self._auth = dict(userId=username, password=password)
        self.headers['Content-Type'] = 'application/json'
        self.verify = False
        self.version = None

        requests.urllib3.disable_warnings()
        self.login()

    def login(self):
        res = self.post('/login/authenticate.do', json=self._auth)
        body = res.json()
        if 'errorCode' in body:
            errmsg = (
                'Unable to login to {server}: {errmsg}. '.format(
                    server=self.host_url,
                    errmsg=body["errorMessage"]
                ) +
                'Check credentials or remote-access reachability.')
            sys.exit(errmsg)

        res = self.get('/cvpInfo/getCvpInfo.do')
        self.version = res.json()['version']
        return self

    def prepare_request(self, request):
        request.url = self.host_url + request.url
        return super(CvpSession, self).prepare_request(request)

    @property
    def about(self):
        return dict(version=self.version,
                    username=self._auth['userId'],
                    host=self.host_url)


def get_inventory():
    api = CvpSession()
    res = api.get('/inventory/devices')
    if not res.ok:
        sys.exit('FAIL: get inventory: ' + res.text)

    ans_inv = defaultdict(dict)
    ans_hosts = ans_inv['_meta']['hostvars'] = defaultdict(dict)
    all_hosts = ans_inv["all"] = {
        "children": [
            "ungrouped"
        ],
        'hosts': [],
    }

    for device in res.json():
        hostname = device['fqdn']
        ipaddr = device['ipAddress']
        ans_hosts[hostname] = dict(
            ansible_host=ipaddr,
            ansible_network_os='eos'
        )
        all_hosts['hosts'].append(hostname)

    return json.dumps(ans_inv)


print(get_inventory())


