#!/usr/bin/env python

# reservation system for lab machines for use in manual or automated testing
#
# this script indicates the reservedness of a machine by the ownership of
# an empty lockfile.
#
# users invoking this script must have set up passwordless ssh access to the
# machines to be managed.
#
# this script is intended to handle concurrency issues only between users;
# simultaneous invocations by the same user may have unpredictable results.

import sys
from subprocess import Popen, PIPE

# constants
# placing the lockfile in /dev/shm/ causes machines to be released on reboot.
LOCKFILE = "/dev/shm/reserved"
# make sure that touch will atomically create non-world-writable files
CHECK_UMASK = "umask -S | sed 's/.*,//g' | grep -v w"

def usage():
    print sys.argv[0], "[release|reserve] [machine...]"
    sys.exit()

def system(args):
    process = Popen(args, stdout=PIPE, stderr=PIPE)
    return process.wait()

def delete_lockfiles(machines):
    for machine in machines:
        system(["ssh", machine, "rm " + LOCKFILE])
        print "released", machine

# check inputs
if len(sys.argv) < 3:
    usage()
option = sys.argv[1]
machines = sys.argv[2:]
for machine in machines:
    if 0 != system(["ssh", machine, CHECK_UMASK]):
        print machine, "is not a valid machine"
        sys.exit(-1)

# manage reservations
if (option == "release"):
    # first, check that this user has all the machines reserved
    for machine in machines:
        if 0 != system(["ssh", machine, "ls " + LOCKFILE]):
            print machine, "was not reserved"
            print "not releasing any machines"
            sys.exit(-1)
        if 0 != system(["ssh", machine, "touch -c " + LOCKFILE]):
            print machine, "is reserved by someone else"
            print "not releasing any machines"
            sys.exit(-1)
    delete_lockfiles(machines)
elif (option == "reserve"):
    reserved = []
    for machine in machines:
        if 0 == system(["ssh", machine, "test -O " + LOCKFILE]):
            # we already had this machine reserved
            print machine, "was already reserved by this user"
            pass
        elif 0 == system(["ssh", machine, "touch " + LOCKFILE]):
            reserved.append(machine)
            print "reserved", machine
        else:
            # clean up after failure
            print machine, "could not be reserved"
            delete_lockfiles(reserved)
            sys.exit(-1)
else:
    usage()
