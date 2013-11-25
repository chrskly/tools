#!/usr/bin/python

''' 
    Very simple script to backup a remote MySQL database.

    Dependencies : python-fabric
'''

import os
import sys
import datetime
import subprocess
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
DEFAULT_PORT = 22

fabric.state.output['running'] = False

def cmd(command, get_ret = True, get_err = True, filter_warnings = False):
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = proc.stdout.read()
    error = ""
    if get_err:
        error = proc.stderr.read()
    returncode = 0
    if get_ret:
        returncode = proc.wait()
    return returncode, output, error

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-l", "--hostname", dest="hostname", help="hostname of server which holds DB from which to backup", metavar="<hostname>")
    parser.add_option("-u", "--user", dest="user", help="username for the DB server", metavar="<user>", default=DEFAULT_USER)
    parser.add_option("-s", "--sqluser", dest="sqluser", help="MySQL username", metavar="<sqluser>")
    parser.add_option("-p", "--password", dest="sqlpass", help="MySQL password", metavar="<sqlpass>")
    parser.add_option("-d", "--database", dest="db", help="DB to be backed up", metavar="<db>")
    parser.add_option("-i", "--keyfile", dest="keyfile", help="Path to ssh key to server", metavar="<pem>", default=DEFAULT_KEY)
    parser.add_option("-t", "--tmpdir", dest="tmpdir", help="Remote tmp path to use when dumping/compressing", metavar="<tmpdir>", default=DEFAULT_TMPDIR)
    parser.add_option("-P", "--port", dest="port", help="SSH port to use to access remote system.", metavar="<port>", default=DEFAULT_PORT)
    parser.add_option("-e", "--events", action="store_true", dest="events", help="Backup MySQL events", default=False)
    parser.add_option("--legacy", dest="legacy", help="Use scp rather than fabric's get() to download files", action="store_true")

    (options, args) = parser.parse_args()

    if not options.hostname or not options.sqluser or not options.sqlpass or not options.db:
        parser.error("You must specify all of -l, -s, -p -d arguments")

    env.timeout = 100000000
    env.user = options.user
    env.key_filename = "%s/%s" % (KEY_PATH, options.keyfile)
    env.port = options.port
    TMPDIR = options.tmpdir

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    # hostname_dbname_timestamp
    tmpfile = "%s/%s_%s_%s.sql" % (TMPDIR, options.hostname, options.db, timestamp)

    with settings(host_string=options.hostname):
        if not files.exists(TMPDIR):
            sudo("mkdir %s" % TMPDIR)
        c = "mysqldump"
        if options.events:
            c += " --events"
        c += " -u %s --routines --quick --single-transaction -p%s %s > %s" % (options.sqluser, options.sqlpass, options.db, tmpfile)
        sudo(c)

        sudo("gzip %s" % tmpfile)

        # Download file to BACKUP_DIR/hostname/
        backup_target = "%s/%s" % (BACKUP_DIR, options.hostname)
        if not os.path.exists(backup_target):
            os.mkdir(backup_target)
        if options.legacy:
            r,o,e = cmd("scp -i %s %s@%s:%s.gz %s" % (env.key_filename, options.user, options.hostname, tmpfile, backup_target))
        else:
            get("%s.gz" % tmpfile, backup_target)

        sudo("rm %s.gz" % tmpfile)

