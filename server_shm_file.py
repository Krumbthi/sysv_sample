# Python modules
import fcntl
import os
import sys

import hashlib

# 3rd party modules
import sysv_ipc
import time
import logging

import globaltimer

# Utils for this demo
import utils


# ----------------------------------------------------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------------------------------------------------
logging.basicConfig(format='%(asctime)s %(name)s %(message)s', level=logging.DEBUG)

PY_MAJOR_VERSION = sys.version_info[0]
GlobTimer = globaltimer.GlobalTimer()

class Server(object):
    def __init__(self):
        self.Logger = logging.getLogger(__class__.__name__)
        self.State = "IDLE"
        self.Cntr = 0
        self.Params = utils.read_params()
        self.CreateFiles()

    def CreateFiles(self):
        self.Logger.debug("Create files")
        os.system("touch %s" % os.path.normpath(self.Params["CMD_FILE"]))
        os.system("touch %s" % os.path.normpath(self.Params["RES_FILE"]))
        with open(os.path.normpath(self.Params["CMD_FILE"]), "w+b") as f:
            f.write(b'\0')

        with open(os.path.normpath(self.Params["RES_FILE"]), "w+b") as f:
            f.write(b'\0')

    def Setup(self):
        self.Logger.debug("Setup")
        try:
            self.Semaphore = sysv_ipc.Semaphore(self.Params["KEY"], sysv_ipc.IPC_CREX)
        except sysv_ipc.ExistentialError as err:
            self.Logger.debug(err)
            # One of my peers created the semaphore already
            self.Semaphore = sysv_ipc.Semaphore(self.Params["KEY"])
            # Waiting for that peer to do the first acquire or release
            while not self.Semaphore.o_time:
                time.sleep(.1)
        else:
            self.Logger.debug("Sem release")
            # Initializing sem.o_time to nonzero value
            self.Semaphore.release()
            # Now the semaphore is safe to use.
                
        self.Logger.debug("Setup done")
        
    def DispatchMsg(self, s):
        #msg = s.encode()

        # try:
        #     assert(msg == hashlib.md5(what_i_wrote).hexdigest())
        # except AssertionError:
        #     raise AssertionError("Shared memory corruption after %d iterations." % i)
        if len(s) > 1:
            #self.Logger.info(s)
            s = s.split(":")[1].lstrip()
            #self.Logger.info(s)
            self.State = s

    def WriteWithLock(self, file_name, msg):
        self.Logger.debug(msg)

        self.Semaphore.acquire()
        with open(file_name, "r+") as f:
            f.write("%s" % msg)
        self.Semaphore.release()

    def Process(self):
        self.Semaphore.release()
        self.Semaphore.acquire()

        with open(os.path.normpath(self.Params["CMD_FILE"]), "r+") as f:
            fd = f.fileno()
            flag = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
            flag = fcntl.fcntl(fd, fcntl.F_GETFL)
            
            #if flag & os.O_NONBLOCK:
            #    print("O_NONBLOCK!!")
            
            res = f.readline()

        self.DispatchMsg(res)

        self.Semaphore.release()

        if self.State == "IDLE":
            self.Logger.debug("State: IDLE")
            self.WriteWithLock(os.path.normpath(self.Params["RES_FILE"]), "Counter: %d" % self.Cntr)
            #self.RespFile.write("Counter: %d" % self.Cntr)
        elif self.State == "INCR":
            self.Logger.debug("State: INCR")
            self.Cntr += 1
            self.WriteWithLock(os.path.normpath(self.Params["RES_FILE"]), "Counter: %d" % self.Cntr)
            #self.RespFile.write("Counter: %d" % self.Cntr)
        elif self.State == "DECR":
            self.Logger.debug("State: DECR")
            self.Cntr -= 1
            self.WriteWithLock(os.path.normpath(self.Params["RES_FILE"]), "Counter: %d" % self.Cntr)
            #self.RespFile.write("Counter: %d" % self.Cntr)
        elif self.State == "QUIT":
            self.Logger.debug("State: QUIT")
            self.Logger.debug("Final release of the semaphore followed by a 5 second pause")
            self.Semaphore.release()
            time.sleep(5)
            # ...before beginning to wait until it is free again.
            self.Logger.debug("Final acquisition of the semaphore")
            self.Semaphore.acquire()

            self.Logger.debug("Destroying semaphore and shared memory")
            
            # TODO: remove file from /dev/shm
            sysv_ipc.remove_semaphore(self.Semaphore.id)
        else:
            self.Logger.debug("Wrong State")
        
    def Cleanup(self):
        self.Logger.debug("Cleanup")
        # TODO: remove file from /dev/shm
        sysv_ipc.remove_semaphore(self.Semaphore.id)


def main():
    serv = Server()
    serv.Setup()

    try:        
        GlobTimer.register_callback(serv.Process)
    except KeyboardInterrupt:
        serv.Cleanup()
        GlobalTimer.unregister_callback(serv.Process)
    
    sys.exit(0)
        

if __name__ == "__main__":
    main()

