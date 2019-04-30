# Python modules
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

    def Setup(self):
        utils.say("Oooo 'ello, I'm Mrs. Premise!")
        self.Params = utils.read_params()
        
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
            # Initializing sem.o_time to nonzero value
            self.Semaphore.release()
            # Now the semaphore is safe to use.

        os.system("touch %s" % os.path.normpath(self.Params["CMD_FILE"]))
        os.system("touch %s" % os.path.normpath(self.Params["RES_FILE"]))

        with open(os.path.normpath(self.Params["CMD_FILE"]), "w+b") as f:
            f.write(42*b'\0')

        with open(os.path.normpath(self.Params["RES_FILE"]), "w+b") as f:
            f.write(42*b'\0')

        self.CmdFile = open(os.path.normpath(self.Params["CMD_FILE"]), "r+")
        self.RespFile = open(os.path.normpath(self.Params["RES_FILE"]), "r+")
        
        self.Logger.debug("Setup done")
        return True

    def DispatchMsg(self, s):
        #msg = s.encode()

        # try:
        #     assert(msg == hashlib.md5(what_i_wrote).hexdigest())
        # except AssertionError:
        #     raise AssertionError("Shared memory corruption after %d iterations." % i)

        self.Logger.debug(s)


    def Process(self):
        # I seed the shared memory with a random value which is the current time.
        what_i_wrote = time.asctime()
        s = what_i_wrote

        #utils.write_to_memory(self.Memory, what_i_wrote)

        utils.say("iteration %d" % self.Cntr)
        self.Cntr += 1

        if not self.Params["LIVE_DANGEROUSLY"]:
            # Releasing the semaphore...
            utils.say("releasing the semaphore")
            self.Semaphore.release()
            utils.say("acquiring the semaphore...")
            self.Semaphore.acquire()

        self.DispatchMsg(utils.read_from_memory(self.Memory))

        if self.State == "IDLE":
            pass
        elif self.State == "INCR":
            pass
        elif self.State == "DECR":
            pass
        elif self.State == "QUIT":
            if not self.Params["LIVE_DANGEROUSLY"]:
                utils.say("Final release of the semaphore followed by a 5 second pause")
                self.Semaphore.release()
                time.sleep(5)
                # ...before beginning to wait until it is free again.
                utils.say("Final acquisition of the semaphore")
                self.Semaphore.acquire()

            utils.say("Destroying semaphore and shared memory")
            # It'd be more natural to call memory.remove() and semaphore.remove() here,
            # but I'll use the module-level functions instead to demonstrate their use.
            sysv_ipc.remove_shared_memory(self.Memory.id)
            sysv_ipc.remove_semaphore(self.Semaphore.id)
        else:
            sysv_ipc.remove_shared_memory(self.Memory.id)
            sysv_ipc.remove_semaphore(self.Semaphore.id)
        
    def Cleanup(self):
        sysv_ipc.remove_shared_memory(self.Memory.id)
        sysv_ipc.remove_semaphore(self.Semaphore.id)


def main():
    serv = Server()

    try:        
        if serv.Setup():
            GlobTimer.register_callback(serv.Process)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        serv.Cleanup()
        GlobalTimer.unregister_callback(serv.Process)
        

if __name__ == "__main__":
    main()

