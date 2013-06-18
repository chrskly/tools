#!/usr/bin/python

''' 
    Very simple script to backup a path from a remote machine.

    Dependencies : python-fabric
'''

import os
import sys
import datetime
import fabric.state
from fabric.api import *
from fabric.contrib import files
from optparse import OptionParser

# The user and key which we use to SSH into the remote system
DEFAULT_USER = "noc"
DEFAULT_KEY = "dotMobi-noc-key.pem"
KEY_PATH = "/home/noc/.ssh/"
# Path on the remote machine to use as tmp space while dumping/compressing
DEFAULT_TMPDIR = "/mnt/tmp"
# Local path to which backup will be saved
BACKUP_DIR = "/backups"

fabric.state.output['running'] = False

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-l", "--hostname", dest="hostname", help="Hostname of server which holds DB from which to backup", metavar="<hostname>")
    parser.add_option("-u", "--user", dest="user", help="Username for the remote system", metavar="<user>", default=DEFAULT_USER)
    parser.add_option("-p", "--path", dest="path", help="Path on remote system to backup", metavar="<path>")
    parser.add_option("-i", "--keyfile", dest="keyfile", help="Path to ssh key to server", metavar="<pem>", default=DEFAULT_KEY)
    parser.add_option("-t", "--tmpdir", dest="tmpdir", help="Remote tmp path to use when dumping/compressing", metavar="<tmpdir>", default=DEFAULT_TMPDIR)

    (options, args) = parser.parse_args()

    if not options.hostname or not options.path:
        parser.error("You must specify both -l and -p arguments, at a minimum")

    env.user = options.user
    env.key_filename = "%s/%s" % (KEY_PATH, options.keyfile)
    TMPDIR = options.tmpdir

    escaped_path = options.path.replace("/", "_")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    # hostname_dbname_timestamp
    tmpfile = "%s/%s_%s_%s.tar" % (TMPDIR, options.hostname, escaped_path, timestamp)

    with settings(host_string=options.hostname):
        if not files.exists(TMPDIR):
            print "mkdir %s" % TMPDIR
            sudo("mkdir %s" % TMPDIR)
        print "tar -C / -cf %s %s" % (tmpfile, options.path.lstrip("/"))
        sudo("tar -C / -cf %s %s" % (tmpfile, options.path.lstrip("/")))

        sudo("gzip %s" % tmpfile)

        # Download file to BACKUP_DIR/hostname/
        backup_target = "%s/%s" % (BACKUP_DIR, options.hostname)
        if not os.path.exists(backup_target):
            os.mkdir(backup_target)
        get("%s.gz" % tmpfile, backup_target)

        sudo("rm %s.gz" % tmpfile)

