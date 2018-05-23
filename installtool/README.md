## installtool
Installtool is a python based CLI utility for scripting "one off" installs of software packages on Linux based servers.
It is more light-weight then your typical CM tool like Puppet or Chef, but since it is "agentless" it does borrow from
the philosophy of Ansible. There are two input components, a configuration file or manifest, composed in YAML and a "blob dir"
which contains artifacts that will be transferred to the host to be configured based on descriptions found in the manifest under the resources section. A nifty feature of this tool is that you can provide a YAML "answer file" to automate the installation of some 3rd party apts that insist on requiring human keyboard interaction.

This tool requires Python 3, the pexpect, yaml, json and inspect libraries


```
usage: installtool.py [-h] [--file FILE] [--blobdir BLOBDIR] [--debug]
                      [--quiet] [--verify] [--threads THREADS]
                      [--loglevel LOGLEVEL]

install a site via remote execution

optional arguments:
  -h, --help            show this help message and exit
  --file FILE, -f FILE  yaml config file
  --blobdir BLOBDIR, -b BLOBDIR
                        If present, directory to get deploy artifacts from
  --debug, -d           Enable various debugging output
  --quiet, -q           silence all output
  --verify, -v          Perform only the verification actions on the host list
  --threads THREADS, -t THREADS
                        perform host actions with M concurrent threads
  --loglevel LOGLEVEL, -l LOGLEVEL
                        Log Level, default is WARN


All installtool configuration files have the following 4 sections:
```
hosts:                # Put a list of Hosts that the actions will be applied to
resources:            # These are files and instaln packabes that live in BLOBDIR
actions:              # How to do the install
verify:               # verify that the install was successful
```

There are currently 5 "operators" available for use in the *actions* section :
```
NOP                   # Just send a \n to the session
XEQ                   # followed by a command to execute remotely
XREM                  # Remove a file from the remote hosts
XFER                  # Transfer a file to the remote host via scp
END                   # Don't expect any more "instructions"
