#!/usr/bin/env python3

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

class ApiHelper(object):
    '''Helper class to do basic login, cookie management, and provide base
    methods to send HTTP requests.  Original code from Dan Wendlandt
    expanded and ported to requests/Pyhton3 by Geoff White

    Copyright [2016] [Ambient Networks LLC]

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.absSee the License for the specific language governing permissions and
    limitations under the License.'''

    def __init__(self, host, port, apiprefix, verify=True):
        self.host = host
        self.port = port
        self.apiprefix = apiprefix
        self.session  = requests.Session()
        self.session.verify = verify
        # If verify=False, don't verifl SSL certificates AND turn off warnings
        if not verify:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        self.urlprefix = None
        self.cookies = None
        self.auth = None

    def request(self, method, op, body="",
                content_type="application/json",
                timeout=0):
        headers = {"Content-Type": content_type}
        requrl = self.urlprefix+op
        to = (timeout if timeout else self.timeout)
        resp = self.session.request(method, requrl, auth=self.auth,
                                    data=body, headers=headers,
                                    timeout=to,
                                    cookies=self.cookies)
        status = resp.status_code
        if status != requests.codes.OK and status != requests.codes.CREATED and\
                status != requests.codes.NO_CONTENT:
            print("Error: %s to %s got unexpected response code"
                   ": %d (content = '%s')"
                   % (method, requrl, status, resp.text))
        return(resp)

    def login(self, logincmd, user="admin", password="admin", timeout=300):
        self.auth = (user, password)
        self.timeout = timeout
        self.urlprefix = "http://%s:%s%s/" % (
            self.host, self.port, self.apiprefix)
    #    resp = self.session.get(url,auth=self.auth, timeout=timeout)
        resp = self.request("get",logincmd)
        self.cookies = resp.cookies
        resp.raise_for_status()
        return resp

    def ws_get(self, url):
        return self.request("GET", url)

    def ws_put(self, url, body):
        return self.request("PUT", url, body)

    def ws_post(self, url, body):
        return self.request("POST", url, body)

    def ws_delete(self, url):
        return self.request("DELETE", url)
