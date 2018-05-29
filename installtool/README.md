## installtool
Installtool is a python based CLI utility for scripting "one-off" installs of software packages on Linux based servers.
It is more light-weight then your typical CM tool like *Puppet* or *Chef*, but since it is *agentless*, it does borrow from the philosophy of Ansible. Unlike Ansible however, the *programming model* is more like assembly language, on the  _retro_ tip.
The manifiest or **runbook** as it is called, is rendered in **YAML** and containes 4 basic sections:
```
hosts:                # Put a list of Hosts that the actions will be applied to
resources:            # These are files and instaln packages that live in BLOBDIR
actions:              # How to do the install
verify:               # verify that the install was successful
```

The **hosts** section specifys a list of Host entries. Each entry is a dict with the following fields:
```

    ip : <addr or fqdn>
    user : <userid>
    password : <string>  OR sshkey : { resource: <key_resource>}
```

The **resources** section contains  *resource definitions*. It is a dictionary where the key is the resource name, and the value is a dict which contains various key-value pairs depending on the value of the mandatory key, **type**. For example:
```
  roguekey :
    type : key-object
    filename : "roguekey.pem"
```
Defines an ssh key resource which is contained in the file named "roguekey.pem". All files that are specified in this section are located in the path specified by the **--blobdir** option on the command line. If that option is missing, then the current working directory is assumed.

The **actions** section consists of an array of arrays. Each individual array element in the actions array is an _instruction_. Instructions have a single operator and can be followed by zero or more _operands_. One way to look at this 
layout, is as an assembly language or microcode program. 
Here's a snippet of "code", that will install Apache, PHP, and load an index.php file into the Web server's html directory.
```
actions:              # How to do the install
  - [NOP]
  - [XEQ, "apt-get --yes update"]
  - [XEQ, "apt-get --yes install php5-common libapache2-mod-php5 php5-cli"]
  - [XFER, file-object: hello]
  - [XFER, file-object: htaccess]
  - [XREM, file-object: indexhtml]
  - [XEQ, "service apache2 restart"]
  - [END]

```
The **XEQ** operator MUST be followed by at least one operand, which is a string containing a bash shell command that will be executed on the remote host. There can also be some optional operands that control certain behavior (like _timeout_ ) or provide resource identifiers which are how files in the BLOBDIR are referenced by the instructions. Here the resource identifiers of the **XFER** instructions, describe various files and where they should be loaded, the resource identifier of the **XREM** instruction, describes the path to a file that needs to be removed.
```
resources:            # These are files and install packages that live in BLOBDIR
  hello :
    type : file-object
    filename : "hello.php"
    user : "root"
    mode : "755"
    destination : "/var/www/html/index.php"

  indexhtml :
    type : file-object
    filename : "index.html"
    user : "root"
    mode : "755"
    destination : "/var/www/html/index.html"

  htaccess :
    type : file-object
    filename : "htaccess"
    user : "root"
    mode : "700"
    destination : "/var/www/html/.htaccess"

```

The **verify** section contains special instructions to verify the results of the operations performed in the **actions** section on each host specified in the **hosts** section. Currently, the only instruction that is available is a simple "health check":
```
CRL                 # operand is an http path, i.e. "/" will perform a GET on http://<host>/
```

There are two input components to the overall tool, a configuration file or runbook, composed in YAML and a "blob dir"
which contains artifacts that will be transferred to the host to be configured based on descriptions found in the runbook under the _resources_ section. A nifty feature of this tool is that you can provide a YAML **answer-file** to automate the installation of some 3rd party apps that insist on requiring human keyboard interaction.

This tool requires Python 3, the pexpect, yaml, json and inspect libraries.


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

There are currently 5 "operators" available for use in the *actions* section :
```
NOP                   # Just send a \n to the session
XEQ                   # followed by a command to execute remotely
XREM                  # Remove a file from the remote hosts
XFER                  # Transfer a file to the remote host via scp
END                   # Don't expect any more "instructions"
```

To get a sense of how the tool works, take a look at *phpinstall.yaml* which will install Apache, PHP, and set an index.php file to display "Hello World!" when you browse to http://<host_name>/. The runbook *gainstall.yaml* together with the answer-file in the *resources* directory *ga570-answers.yaml* is an example of using the tool to install a third party app that requires human interaction, in this case, the GoAnywhere MFT.

The command
```
installtool.py -df phpinstall.yaml -b resources
```
Will perform the runbook *phpinstall.yaml* with verbose output utilizing resources that will be found in the directory *resources*

Enjoy and Deploy!
