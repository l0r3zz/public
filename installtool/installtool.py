#Copyright (c) 2018 Geoffrey White
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import argparse
import sys
import yaml
import json
import pexpect
from pexpect import pxssh
import os
import inspect
import concurrent.futures


#############################   Globals  ######################################
Debug = False
###############################################################################

#############################   Class Definitions  ############################


class Session:
    """Instantiate a remote ssh session via pexpect and use it to perform all
    actions"""
    def __init__(self, ip, uid, usepass=None, key=None, debug=False):
        self.host = ip
        self.uid = uid
        self.passwd = usepass
        self.sshkey = key
        self.debug = debug
        if usepass:
            self.passwd = usepass
        elif key:
            self.sshkey = key
        try:
            s = pxssh.pxssh()
            s.login(self.host, self.uid, password=self.passwd,
                    ssh_key=self.sshkey, login_timeout=30)
        except pexpect.pxssh.ExceptionPxssh as e:
            print("pxssh failed on login")
            print(e)
        self.ses = s

class InstalltoolOps:
    """ Class to hold all action operators so that we can leverage inspect"""
    def __init__(self):
        self.func_dict = {}
        for func in dir(self) :
            if not func.startswith('_') and eval(
                ("hasattr( self.%s,'__call__')") % func):
                self.func_dict[func] = eval(
                    "inspect.getargspec(self.%s)" % func )

    def _xeq_op(self,s, r, op):
        """ This is the internl execution function that allows us to do away
        with the if-elif tree in the upstream xeq function. It is not enumerated
        by __init__ when the function table is created.  This allows for the easy
        extension of user exposed functionality by just adding new functions
        to this Class.
        """
        try:
            op_spec = self.func_dict[op[0]]
        except KeyError :
            print("Installtool: Operator %s not found, ignoring" % (op[0]))
            return False
        eval_cmd = "self.%s(s,r,op)" % op[0]
        result = eval(eval_cmd)
        return result

    def NOP(self,s,r,op):
        s.ses.sendline("")
        s.ses.prompt()
        if Debug:
            print("[%s] NOP: %s" % (s.host, s.ses.before))
        return True

    def XFER(self,s,r,op):
        host = s.host
        user = s.uid
        pw = s.passwd
        res_dict = r["resources"][op[1]["resource"]]
        file = r["blobdir"] + "/" + res_dict["filename"]
        dest = res_dict["destination"]
        xfrcmd = "/usr/bin/scp -q %s %s@%s:%s" % (file, user, host, dest)
        (output,status) = pexpect.run(xfrcmd,
                                      events={"password: ":pw+'\n'},
                                      withexitstatus=1)
        if status :
            print("XFER: file not transferred")
        if Debug:
            print("[%s] XFER: %s status: %s" % (s.host, file, status))
        return True

    def XREM(self,s,r,op):
        res_dict = r["resources"][op[1]["resource"]]
        target = res_dict["destination"]
        s.ses.sendline("rm -f %s" % (target))
        s.ses.prompt()
        if Debug:
            print("[%s] XREM: %s" % (s.host, s.ses.before))
        return True

    def XEQ(self,s,r,op):
        s.ses.sendline(op[1])
        s.ses.prompt()
        if Debug:
            print("[%s] XEQ: %s" % (s.host, s.ses.before))
        return True

    def END(self,s,r,op):
        s.ses.sendline("")
        s.ses.prompt()
        if Debug:
            print("[%s] END: %s" % (s.host, s.ses.before))
        return False

###############################################################################
################# These are debugging helper functions ########################


def pretty_print(obj, ofd=sys.stdout):
    json.dump(obj, ofd, sort_keys=True, indent=4)
    ofd.flush()


def pretty_prints(str, ofd=sys.stdout):
    ofd.write("'")
    json.dump(json.loads(str), ofd, sort_keys=True, indent=4)
    ofd.write("'")
    ofd.flush()


def std_prints(str, ofd=sys.stdout):
    ofd.write("'")
    json.dump(json.loads(str), ofd)
    ofd.write("'")
    ofd.flush()


###############################################################################
#############################   verify operators           ####################

def CRL(h,rb,op):
    host = h["ip"]
    endpoint = op[1]
    crlcmd = "curl -q -i http://%s/%s" % (host, endpoint)
    (output,status) = pexpect.run(crlcmd,withexitstatus=1)
    status_line = (output.splitlines()[0].decode("utf-8")
                   + " / " + output.splitlines()[14].decode("utf-8"))
    print("[%s]:%s" % (host,status_line))
    if status :
        print("CRL: %s FAIL" % (crlcmd))

    if Debug:
        print("[%s] CRL: %s status: %s" % (host, output, status))
    return True
###############################################################################
#############################   main function Definitions  ####################
def read_config(av):
    """ Load the config file (runbook)"""
    config_path = av.file
    if os.path.exists(config_path):
        rb = yaml.load(open(config_path))
        rb["blobdir"] = av.blobdir # for processes that need it
        rb["threads"] = av.threads # for processes that need it
        rb["verify-only"] = av.verify # for processes that need it
    else:
        rb = {}
    return rb


def process_runbook(rb):
    """Perform the 'actions' across all 'hosts' using the supplied 'resources'"""

    def xeq(s,rb, action_list):
        """Execute a list of operations through the provided session with runbook"""
        thread = InstalltoolOps()
        for op in action_list:
            if not thread._xeq_op(s,rb,op):
                break
        print("[%s]" % (s.host))
        return


    def vfy(h, rb, action_list):
        """Execute a list of verification steps on localhost in the runbook"""
        for op in action_list:
            if op[0] == "CRL":
                CRL(h,rb,op)
                continue
        return

    def thrd(host):
        if "password" in host:
            session = Session(host['ip'], host['user'], password=host['password'])
        elif "sshkey" in host:
            key_resource = host["sshkey"]["resource"]
            keyfile = rb["blobdir"] + "/" + rb["resources"][key_resource]["filename"]
            session = Session(host['ip'], host['user'], key=keyfile)
        else:
            print("[%s]: No account authentication method provided" % host["ip"])
            return
        xeq(session, rb, rb["actions"])

    if not rb["verify-only"]:
        print("Remediating Hosts")
        with concurrent.futures.ThreadPoolExecutor(max_workers=rb["threads"]) as pool:
            thread_results = list(pool.map(thrd,rb["hosts"]))
    print("Verifying Hosts")
    for host in rb['hosts']:
        vfy(host, rb, rb["verify"])
    return 0


###############################################################################
def main():
    """
    usage: installtool.py [-h] [--file FILE] [--blobdir BLOBDIR] [--debug]
                      [--verify]
    """

    def get_opts():
        parser = argparse.ArgumentParser(
            description="install a site via remote execution")
        parser.add_argument('--file', "-f", default="-",
                            help="yaml config file")
        parser.add_argument('--blobdir', "-b", default=".",
                     help="If present, directory to get deploy artifacts from")
        parser.add_argument('--debug', "-d", action="store_true",
                     help="Enable various debugging output")
        parser.add_argument('--verify', "-v", action="store_true",
                     help="Perform only the verification actions on the host list")
        parser.add_argument('--threads', "-t", type=int, default=1,
                     help="perform host actions with M concurrent threads")
        args = parser.parse_args()
        return args

    argv = get_opts()
    global Debug
    Debug = argv.debug
    runbook = read_config(argv)
    process_runbook(runbook)
    if Debug:
        pretty_print(runbook)
    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)
