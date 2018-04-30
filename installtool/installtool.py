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
import re


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
            s.login(self.host, self.uid, self.passwd,login_timeout=30)
        except pexpect.pxssh.ExceptionPxssh as e:
            print("pxssh failed on login")
            print(e)
        self.ses = s

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
#############################   actions operators          ####################


def NOP(s,r):
    s.ses.sendline("")
    s.ses.prompt()
    if Debug:
        print("[%s] NOP: %s" % (s.host, s.ses.before))
        return True
###############################################################################
#############################   main function Definitions  ####################
def read_config(av):
    """ Load the config file (runbook)"""
    config_path = av.file
    if os.path.exists(config_path):
        rb = yaml.load(open(config_path))
        rb["argvec"] = av # for processe that need it
    else:
        rb = {}
    return rb


def process_runbook(rb):
    """Perform the 'actions' across all 'hosts' using the supplied 'resources'"""

    def xeq(s,rb, action_list):
        """Execute a list of operations through the provided session with runbook"""
        for op in action_list:
            if op[0] == "NOP":
                NOP(s, rb)
                continue
            elif op[0] == "END":
                break
            elif op[0] == "XFER":
                host = s.host
                user = s.uid
                pw = s.passwd
                res_dict = rb["resources"][op[1]["resource"]]
                file = rb["argvec"].blobdir + "/" + res_dict["filename"]
                dest = res_dict["destination"]
                xfrcmd = "/usr/bin/scp -q %s %s@%s:%s" % (file, user, host, dest)
                (output,status) = pexpect.run(xfrcmd,events={"password: ":pw+'\n'},withexitstatus=1)
                if status :
                    print("XFER: file not transferred")
                if Debug:
                    print("[%s] XFER: %s status:" % (s.host, file, status))

                continue
        return

    for host in rb['hosts']:
        session = Session(host['ip'], host['user'], host['password'])
        xeq(session, rb, rb["actions"])
    return 0


###############################################################################
def main():
    """
    usage: installtool.py [-h] [--file FILE] [--blobdir BLOBDIR] [--debug]

    install a site via remote execution

    optional arguments:
      -h, --help            show this help message and exit
      --file FILE, -f FILE  yaml config file
      --blobdir BLOBDIR, -b BLOBDIR
                            If present, directory to get deploy artifacts from
      --debug, -d           Enable various debugging output

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
