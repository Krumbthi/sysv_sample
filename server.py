# Python modules
import sys
import hashlib

# 3rd party modules
import sysv_ipc
import time
import timer

# Utils for this demo
import utils

PY_MAJOR_VERSION = sys.version_info[0]
GlobTimer = timer.GlobalTimer()

class Server(object):
    def __init__(self):
        utils.say("Oooo 'ello, I'm Mrs. Premise!")
        self.Params = utils.read_params()
        self.Semaphore = sysv_ipc.Semaphore(self.Params["KEY"], sysv_ipc.IPC_CREX)
        self.Memory = sysv_ipc.SharedMemory(self.Params["KEY"], sysv_ipc.IPC_CREX)
        self.State = "IDLE"

    def Process(self):
        # I seed the shared memory with a random value which is the current time.
        what_i_wrote = time.asctime()
        s = what_i_wrote

        utils.write_to_memory(self.Memory, what_i_wrote)

        if self.State == "IDLE":
            utils.say("iteration %d" % i)
            if not self.Params["LIVE_DANGEROUSLY"]:
                # Releasing the semaphore...
                utils.say("releasing the semaphore")
                self.Semaphore.release()
                # ...and wait for it to become available again. In real code it'd be
                # wise to sleep briefly before calling .acquire() in order to be
                # polite and give other processes an opportunity to grab the semaphore
                # while it is free and thereby avoid starvation. But this code is meant
                # to be a stress test that maximizes the opportunity for shared memory
                # corruption, and politeness has no place in that.
                utils.say("acquiring the semaphore...")
                self.Semaphore.acquire()

            s = utils.read_from_memory(self.Memory)
            
        elif self.State == "INCR":
            pass
        elif self.State == "DECR":
            pass
        else:
            pass

        for i in range(0, self.Params["ITERATIONS"]):
            utils.say("iteration %d" % i)
            if not self.Params["LIVE_DANGEROUSLY"]:
                # Releasing the semaphore...
                utils.say("releasing the semaphore")
                self.Semaphore.release()
                # ...and wait for it to become available again. In real code it'd be
                # wise to sleep briefly before calling .acquire() in order to be
                # polite and give other processes an opportunity to grab the semaphore
                # while it is free and thereby avoid starvation. But this code is meant
                # to be a stress test that maximizes the opportunity for shared memory
                # corruption, and politeness has no place in that.
                utils.say("acquiring the semaphore...")
                self.Semaphore.acquire()

            s = utils.read_from_memory(self.Memory)

            # I keep checking the shared memory until something new has been written.
            while s == what_i_wrote:
                if not self.Params["LIVE_DANGEROUSLY"]:
                    utils.say("releasing the semaphore")
                    self.Semaphore.release()
                    utils.say("acquiring the semaphore...")
                    self.Semaphore.acquire()

                # Once the call to .acquire() completes, I own the shared resource and
                # I'm free to read from the memory.
                s = utils.read_from_memory(self.Memory)

            # What I read must be the md5 of what I wrote or something's gone wrong.
            if PY_MAJOR_VERSION > 2:
                what_i_wrote = what_i_wrote.encode()

            try:
                assert(s == hashlib.md5(what_i_wrote).hexdigest())
            except AssertionError:
                raise AssertionError("Shared memory corruption after %d iterations." % i)

            # MD5 the reply and write back to Mrs. Conclusion.
            if PY_MAJOR_VERSION > 2:
                s = s.encode()
            what_i_wrote = hashlib.md5(s).hexdigest()
            utils.write_to_memory(self.Memory, what_i_wrote)


        # Announce for one last time that the semaphore is free again so that
        # Mrs. Conclusion can exit.
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

def main():
    serv = Server()
    GlobTimer.register_callback(serv.Process)


if __name__ == "__main__":
    main()

