import os
import argparse
import sys
import yaml
import json
import pexpect


def read_config(av):
    config_path = av.blobdir+av.file
    if os.path.exists(config_path):
        r = yaml.load(file(config_path))
    else:
        r = {}
    return r


def process_runbook(r):
    return 0


def main():
    """
usage: installtool.py [-h] [--file FILE] [--blobdir BLOBDIR]

install a site via remote execution

optional arguments:
  -h, --help            show this help message and exit
  --file FILE, -f FILE  yaml config file
  --blobdir BLOBDIR, -b BLOBDIR
                        If present, directory to get deploy artifacts from
    """

    def get_opts():
        parser = argparse.ArgumentParser(
            description="install a site via remote execution")
        parser.add_argument('--file', "-f", default="-",
                            help="yaml config file")
        parser.add_argument('--blobdir', "-b", default="./",
                     help="If present, directory to get deploy artifacts from")
        args = parser.parse_args()
        return args

    argv = get_opts()
    runbook = read_config(argv)
    process_runbook(runbook)
    print(json.dumps(runbook))
    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)
