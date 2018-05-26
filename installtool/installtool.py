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
###
##
#   installtool: A quick and easy "CM" program designed to  remotely install
#   programs on linux platforms, expecially programs that require human
#   interaction. This is accomplished by the use of yaml "runbooks" that
#   define the list of hosts to remediate, the actions to perform to achieve
#   the remediation and any verification steps to perform afterwards. Programs
#   that expect human interaction can have and yaml "answer-file" provided
#   which provides responses to expected output

import argparse
import sys
import yaml
import json
import pexpect
from pexpect import pxssh
import os
import inspect
import concurrent.futures
import mylog


#############################   Globals  ######################################
Debug = False
Log = None
Quiet = False
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
            s.login(self.host, self.uid, self.passwd,
                    ssh_key=self.sshkey, login_timeout=30)
        except pexpect.pxssh.ExceptionPxssh as e:
            Log.error("pxssh failed on login %s" % e)
        self.ses = s
        self.ses.PROMPT ="[\$\#]"

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
        with the if-elif tree in the upstream xeq function. It references
        the func_dict dictionary where actions are entered by by __init__ when
        the function table is created.  This allows for the easy
        extension of user exposed functionality by just adding new functions
        to this Class.
        All actions must have the same calling structure:
            OP([self], s, r, op)
            where:
                s     is the Session Object the OP operates on
                r     is a pointer to the runbook datastructure
                op    is the list of the current instruction, op and operands

        """
        try:
            op_spec = self.func_dict[op[0]]
        except KeyError :
            Log.error("Installtool: Operator %s not found, ignoring" % (op[0]))
            return False
        eval_cmd = "self.%s(s,r,op)" % op[0]
        result = eval(eval_cmd)
        return result

    def _get_operands(self,s,r,op):
        """ This internal function processes any qualifying operands
        and binds the values to specific variables that the Operators
        use in execution, like timeout duration, or resource specifications
        """
        to = 30
        k_o = None
        f_o = None
        a_o = None
        for operand in op:
            (k,v), = operand.items()
            if k == "timeout":
                to = v
            elif k == "key-object":
                k_o = r["resources"][v]
            elif k == "file-object":
                f_o = r["resources"][v]
            elif k == "answer-object":
                a_o = r["resources"][v]
            else:
                 Log.error("unknown operand %s" % r["resources"][v])
        return to, k_o, f_o, a_o

    def NOP(self,s,r,op):
        """ Send a newline and look for a prompt"""
        s.ses.sendline("")
        s.ses.prompt()
        if Debug:
            Log.debug("[%s] NOP: %s" % (s.host, s.ses.before))
        return True

    def XFER(self,s,r,op):
        """ Transfer a file using scp from the host running installtool
        to a destination host somewhere on the internet
        """
        if Debug:
            Log.debug("[%s] %s: START %s" % (s.host,op[0],op[1]))
        host = s.host
        user = s.uid
        pw = s.passwd
        key = s.sshkey

        to = 30
        key_object = None
        file_object = None
        answer_object = None

        if len(op) > 1:
            to,key_object,file_object,answer_object = (
                self._get_operands(s,r,op[1:]))

        file = r["blobdir"] + "/" + file_object["filename"]
        dest = file_object["destination"]
        if "installdir" in file_object:
            target = file_object["installdir"]
        else:
            target = file_object["destination"]
        if s.passwd:
            xfrcmd = "/usr/bin/scp -q %s %s@%s:%s" % (file, user, host, target)
            (output,status) = pexpect.run(xfrcmd,
                                          events={"password: ":pw+'\n'},
                                          timeout=to, withexitstatus=1)
        elif s.sshkey:
            xfrcmd = "/usr/bin/scp -q -i %s %s %s@%s:%s" % (
                key, file, user, host, target)
            (output,status) = pexpect.run(xfrcmd, timeout=to,  withexitstatus=1)
        if status :
            Log.error("XFER: file not transferred")
        if "installdir" in file_object:
            # if not root, we have to scp then move it into place
            installfile = target + "/" + file_object["filename"]
            mvop =[ "XEQ", "cmd"]
            mvop[1] = "sudo mv %s %s" % (installfile,  dest)
            self.XEQ(s,r,mvop)
        if Debug:
            Log.debug("[%s] XFER: %s status: %s" % (s.host, file, status))
        return True

    def XREM(self,s,r,op):
        """ Remove a file from the remote host"""
        if Debug:
            Log.debug("[%s] %s: START %s" % (s.host,op[0],op[1]))
        to = 30
        key_object = None
        file_object = None
        answer_object = None

        if len(op) > 1:
            to,key_object,file_object,answer_object = (
                self._get_operands(s,r,op[1:]))
        target = file_object["destination"]
        if s.passwd:
            s.ses.sendline("rm -f %s" % (target))
        elif s.sshkey:
            s.ses.sendline("sudo rm -f %s" % (target))
        s.ses.prompt()
        if Debug:
            Log.debug("[%s] XREM: %s" % (s.host, s.ses.before))
        return True

    def XEQ(self,s,r,op):
        """ Perform a cli command on the remote host"""
        if Debug:
            Log.debug("[%s] %s: START %s" % (s.host,op[0],op[1]))
        to = 30
        key_object = None
        file_object = None
        answer_object = None

        if len(op) > 2:
            to,key_object,file_object,answer_object = (
                self._get_operands(s,r,op[2:]))
        if answer_object :
            answerfile = r["blobdir"] + "/" + answer_object["filename"]
            try:
                answerlist = yaml.load(open(answerfile))
            except (FileNotFoundError,
                    yaml.scanner.ScannerError) as err:
                Log.error("Error:%s" % err)
                sys.exit(1)

            s.ses.sendline(op[1])
            index =0
            for ans in answerlist["answers"]:
                (k,v), = ans.items()
                rstatus = s.ses.expect(
                    [k,pexpect.TIMEOUT,pexpect.EOF],timeout=to)
                if v =='\n':
                    s.ses.sendline('')
                else:
                    s.ses.sendline(v)
                if rstatus == 0:
                    continue
                elif rstatus == 1:
                    Log.error("Answer timed out at answer %d ,aborting" % index)
                else:
                    Log.error("Channel closed prematurely at answer %d" % index)
                index = index+1
            s.ses.prompt(timeout=to)
        else:
            s.ses.sendline(op[1])
            s.ses.prompt(timeout=to)
        if Debug:
            Log.debug("[%s] XEQ: %s" % (s.host, s.ses.before))
        return True

    def END(self,s,r,op):
        """ Send a newline and look for a prompt but always return False"""
        s.ses.sendline("")
        s.ses.prompt()
        if Debug:
            Log.debug("[%s] END: %s" % (s.host, s.ses.before))
        return False

###############################################################################
################# These are debugging helper functions ########################


def pretty_print(obj, ofd=sys.stdout):
    """ Dump a Python datastructure to a file (stdout is the default)
    in a human friendly way"""
    json.dump(obj, ofd, sort_keys=True, indent=4)
    ofd.flush()


def pretty_prints(str, ofd=sys.stdout):
    """ Dump a json string to a file (stdout is the default)
    in a human friendly way"""
    ofd.write("'")
    json.dump(json.loads(str), ofd, sort_keys=True, indent=4)
    ofd.write("'")
    ofd.flush()


def std_prints(str, ofd=sys.stdout):
    """ Dump a json string to a file (stdout is the default)"""

    ofd.write("'")
    json.dump(json.loads(str), ofd)
    ofd.write("'")
    ofd.flush()


###############################################################################
#############################   verify operators           ####################

def CRL(h,rb,op):
    """SInple URL health-check using curl, prints HTTP response and 1st
    line of the response payload"""
    host = h["ip"]
    endpoint = op[1]
    crlcmd = "curl -q -i http://%s/%s" % (host, endpoint)
    (output,status) = pexpect.run(crlcmd,withexitstatus=1, timeout=5)
    if not Quiet and output:
        status_line = (output.splitlines()[0].decode("utf-8")
                   + " / " + output.splitlines()[-1].decode("utf-8"))
        print("[%s]:%s" % (host,status_line))
    if not output and not Quiet:
        print("CRL: %s FAIL" % (crlcmd))

    if Debug:
        Log.debug("[%s] CRL: %s status: %s" % (host, output, status))
    return True
###############################################################################
#############################   main function Definitions  ####################
def read_config(av):
    """ Load the config file (runbook)"""
    config_path = av.file
    if os.path.exists(config_path):
        try:
            rb = yaml.load(open(config_path))
        except yaml.scanner.ScannerError as err:
            Log.error("Error:%s" % err)
            sys.exit(1)
        rb["blobdir"] = av.blobdir # for processes that need it
        rb["threads"] = av.threads # for processes that need it
        rb["verify-only"] = av.verify # for processes that need it
    else:
        Log.error("No runbook file found at %s" % config_path)
        sys.exit(1)
    return rb


def process_runbook(rb):
    """Perform the 'actions' across all 'hosts' using the supplied
    'resources'"""

    def xeq(s,rb, action_list):
        """Execute a list of operations through the provided session
        with runbook"""
        if not Quiet:
            print("[%s]" % (s.host))
        thread = InstalltoolOps()
        for op in action_list:
            if not thread._xeq_op(s,rb,op):
                break
        return


    def vfy(h, rb, action_list):
        """Execute a list of verification steps on localhost in the runbook"""
        if not action_list:
            return
        for op in action_list:
            if op[0] == "CRL":
                CRL(h,rb,op)
                continue
        return

    def thrd(host):
        """ Workhorse function that connects to the reomte host, performs
        a login and sequentially performs all 'actions' through that session"""
        if "password" in host:
            session = Session(host['ip'], host['user'], host['password'])
        elif "sshkey" in host:
            key_resource = host["sshkey"]["resource"]
            keyfile = (rb["blobdir"] + "/" +
                       rb["resources"][key_resource]["filename"])
            session = Session(host['ip'], host['user'], key=keyfile)
        else:
            Log.error("[%s]: No account authentication method provided"
                      % host["ip"])
            return
        xeq(session, rb, rb["actions"])
        return

    if not rb["verify-only"]:
        if not Quiet:
            print("Remediating Hosts")
        # If you use the "-t" flag, hosts remediation will be done in parallel
        # using NUM threads where -t NUM is specified, else hosts are processed
        # sequentially.
        if rb["threads"]:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=rb["threads"]) as pool:
                thread_results = list(pool.map(thrd, rb["hosts"]))
        else:
            for host in rb["hosts"]:
                thrd(host)

    if not Quiet:
        print("Verifying Hosts")
    for host in rb['hosts']:
        vfy(host, rb, rb["verify"])
    return 0


###############################################################################
def main():
    """
    Program main loop
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
        parser.add_argument('--quiet', "-q", action="store_true",
                     help="silence all output")
        parser.add_argument('--verify', "-v", action="store_true",
                     help="Perform only the verification actions on the host list")
        parser.add_argument('--threads', "-t", type=int, default=0,
                     help="perform host actions with M concurrent threads")
        parser.add_argument('--loglevel', "-l", default="WARN",
                     help="Log Level, default is WARN")
        args = parser.parse_args()
        return args

    argv = get_opts()
    global Debug
    global Log
    global Quiet
    Debug = argv.debug
    if Debug:
        loglevel = "DEBUG"
    else:
        loglevel = argv.loglevel
    if argv.quiet:
        Quiet = True
        devnull = open("/dev/null","w")
        Log = mylog.logg("installtool", cnsl=True, llevel=loglevel, sh=devnull)
    else:
        Log = mylog.logg("installtool", cnsl=True, llevel=loglevel)
    runbook = read_config(argv)
    process_runbook(runbook)
    if Debug and not Quiet:
        pretty_print(runbook)
    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)
