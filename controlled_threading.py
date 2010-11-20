# Populate namespace with default objects from threading and modify as needed
from threading import * #@UnusedWildImport
import threading as original_threading

import greenlet

# TODO: remove this when no longer debugging
def NOP():
    pass

greenlet_list = []
control_greenlet = greenlet.getcurrent()

def get_greenlet_list():
    return greenlet_list


def are_greenlets_alive():
    live_greenlets = [greenlet for greenlet in greenlet_list if not greenlet.dead]
    return len(live_greenlets) != 0


def start_greenlet_from_file(filename, execution_path_to_run=None):
    cancel_all_greenlets()

    def run_as_main(filename):
        # modify globals so it looks like filename is being run as main
        g = globals()
        g['__name__'] = '__main__'

        # execute file with modified globals dictionary
        execfile(filename, g)

    new_greenlet = greenlet.greenlet(run_as_main)
    greenlet_list.append(new_greenlet)
    new_greenlet.switch(filename)

    if execution_path_to_run:
        for step in execution_path_to_run:
            greenlet_list[step].switch()


def cancel_all_greenlets():
    for greenlet in greenlet_list[:]: # use copy since this loop will modify the contents
        if greenlet:
            try:
                greenlet.throw(KeyboardInterrupt)
            except KeyboardInterrupt:
                pass

        greenlet_list.remove(greenlet)


class Thread(object):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        self.group = group
        self.target = target
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def start(self):
        # create greenlet and then "run" it
        self.greenlet = greenlet.greenlet(run=self.run, parent=control_greenlet)
        greenlet_list.append(self.greenlet)

        # begin greenlet execution
        self.greenlet.switch()

    def run(self):
        # switch to control greenlet so that scheduling can be forced
        control_greenlet.switch(greenlet.getcurrent())

        # begin actual execution
        self.target(*self.args, **self.kwargs)

    def join(self):
        while self.isAlive():
            control_greenlet.switch(greenlet.getcurrent())
            NOP()

    def isAlive(self):
        return not self.greenlet.dead


class Lock(object):
    def __init__(self):
        self.lock = original_threading.Lock()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False

    def acquire(self, blocking=1):
        control_greenlet.switch(greenlet.getcurrent())
        NOP()

        return self.lock.acquire(blocking)

    def release(self):
        return self.lock.release()

# Python apparently expects the 'threading' module to have a _shutdown method
#  without this you'll always get an error on exit
def _shutdown():
    pass
