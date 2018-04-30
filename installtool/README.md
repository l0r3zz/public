## installtool
Installtool is a python based CLI utility for scripting "one off" installs of software packages on Linux based servers.
It is more light-weight then your typical CM tool like Puppet or Chef, but since it is "agentless" it does borrow from
the philosophy of Ansible. There are two input components, a configuration file or manifest, composed in YAML and a "blob dir"
which contains artifacts that will be transferred to the host to be configured based on descriptions found in the manifest under the resources section.

This tool requires Python 3, the pexpect, yaml, json and inspect libraries


```usage: installtool.py [-h] [--file FILE] [--blobdir BLOBDIR] [--debug]
                      [--verify]

install a site via remote execution

optional arguments:
  -h, --help            show this help message and exit
  --file FILE, -f FILE  yaml config file
  --blobdir BLOBDIR, -b BLOBDIR
                        If present, directory to get deploy artifacts from
  --debug, -d           Enable various debugging output
  --verify, -v          Perform only the verification actions on the host list

```

All installtool configuration files have the following 4 sections:
```
hosts:                # Put a list of Hosts that the actions will be applied to
resources:            # These are files and instaln packabes that live in BLOBDIR
actions:              # How to do the install
verify:               # verify that the install was successful
```
