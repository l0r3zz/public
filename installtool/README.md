## installtool
Installtool is a python based CLI utility for scripting "one off" installs of software packages on Linux based servers.
It is more light-weight then your typical CM tool like *Puppet* or *Chef*, but since it is *agentless*, it does borrow from the philosophy of Ansible. But unlike Ansible, the *programming model* is more like assembly language, on the  _retro_ tip.
The manifiest is rendered in **YAML** and containes 4 basic sections:
```
hosts:                # Put a list of Hosts that the actions will be applied to
resources:            # These are files and instaln packabes that live in BLOBDIR
actions:              # How to do the install
verify:               # verify that the install was successful
```

The **hosts** section specifys a list of Host entries, each entry is a dict with the fillowing fields:
```

    ip : <addr or fqdn>
    user : <userid>
    password : <string>  OR sshkey : { resource: <key_resource>}
```

The **resources** section contains  *resource definition*. It is a dictionary where the key is the resource name, and the value is a dict which contains various key-value pairs, depending on the value of the mandatory key **type**, for example:
```
  roguekey :
    type : key-object
    filename : "roguekey.pem"
```
Defines an ssh key resource which is contained in the file named "roguekey.pem". All files that are specified in this section are located in the path specified by the **--blobdir** option on the command line. If that option is missing, then the current working directory is assumed.

The **actions** section consists of an array of arrays. Each individual array element in the action array is an _instruction_, Which has a single operator and is followed by zero or more _operands_. The XEQ operator MUST be followed by at least one operand, which is a string containing a bash shell command that will be executed on the remote host. There can also be some optional operands that control certain behavior (like _timeout_ ) or provide resource identifiers which are how files in the BLOBDIR are referenced by the instructions.

The **verify** section contains special instructions to verify the results of the operations performed in the **actions** section on each host specified in the **hosts** section. Currently the only instruction that is available is a simple "health check":
```
CRL                 # operand is an http path, i.e. "/" will perform a GET on http://<host>/
```

There are two input components to the overall tool, a configuration file or manifest, composed in YAML and a "blob dir"
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
```

All installtool configuration files have the following 4 sections:


There are currently 5 "operators" available for use in the *actions* section :
```
NOP                   # Just send a \n to the session
XEQ                   # followed by a command to execute remotely
XREM                  # Remove a file from the remote hosts
XFER                  # Transfer a file to the remote host via scp
END                   # Don't expect any more "instructions"
```
