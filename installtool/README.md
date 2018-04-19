## installtool
Installtool is a python based CLI utility for scripting "one off" installs of software packages on Linux based servers.
It is more light-weigh then your typical CM tool, like Puppet or Chef, but since it is "agentless" it does borrow from
the philosophy of Ansible. THere are two input components, a configuration file or manifest, composed in YAML and a "blob dir"
which contains artifacts that will be transferred to the host to be configured:


```usage: installtool.py [-h] [--file FILE] [--blobdir BLOBDIR]

install a site via remote execution

optional arguments:
  -h, --help            show this help message and exit
  --file FILE, -f FILE  yaml config file
  --blobdir BLOBDIR, -b BLOBDIR
                        If present, directory to get deploy artifacts from
```

All installtool configuration files have the following 4 sections:
```
hosts:                # Put a list of Hosts that the actions will be applied to
resources:            # These are files and instaln packabes that live in BLOBDIR
actions:              # How to do the install
verify:               # verify that the install was successful
```
