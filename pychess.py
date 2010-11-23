import sys
import controlled_threading

# install controlled_threading in sys.modules so future imports get this module 
#    Note to pydev users: add a breakpoint on the following line to make all 
#    your troubles go away (haven't investigated why this works, but it does)
sys.modules['threading'] = controlled_threading

greenlet_list = controlled_threading.get_greenlet_list()


class RunStorage(object):
    def __init__(self):
        self.fail_paths = []
        self.complete_paths = []
        self.depth_limited_paths = []
        self.context_limited_paths = []
        
        self.execution_history = []
        
        self.last_greenlet_run = None
        self.file_being_run = None
    

def run_interleavings(max_switches, max_depth, storage):
    if not controlled_threading.are_greenlets_alive():
        storage.last_greenlet_run = \
            controlled_threading.start_greenlet_from_file(storage.file_being_run,
                                                          storage.execution_history)

    for stepIndex in xrange(len(greenlet_list)): # use indices since greenlet_list will change each iteration
        if not controlled_threading.are_greenlets_alive():
            storage.last_greenlet_run = \
                controlled_threading.start_greenlet_from_file(storage.file_being_run,
                                                              storage.execution_history)
        
        storage.execution_history.append(stepIndex)

        try:
            if storage.execution_history in storage.complete_paths + storage.depth_limited_paths + storage.fail_paths:
                print "%s: skipping (path already run)" % (storage.execution_history)
                continue

            greenlet = greenlet_list[stepIndex]
            
            if not greenlet:
                print "%s: skipping (greenlet %s already completed)" % (storage.execution_history, stepIndex)
                continue

            if greenlet != storage.last_greenlet_run:
                if max_switches is 0:
                    storage.context_limited_paths.append(storage.execution_history[:])
                    print "%s: skipping (exceeds context bound)" % storage.execution_history
                    continue
                switches_left = max_switches - 1
            else:
                switches_left = max_switches

            try:            
                storage.last_greenlet_run = greenlet.switch()
            except AssertionError, e:
                storage.fail_paths.append(storage.execution_history[:])
                print "%s: test failure (%s)" % (storage.execution_history, e)
                continue
            else:
                if not controlled_threading.are_greenlets_alive():
                    storage.complete_paths.append(storage.execution_history[:])
                    print "%s: finished (all greenlets completed)" % storage.execution_history
                    continue
                
                if max_depth <= 1:
                    storage.depth_limited_paths.append(storage.execution_history[:])
                    print "%s: aborting (depth limit reached)" % storage.execution_history
                    continue
                
                run_interleavings(switches_left, max_depth - 1, storage)

            finally:
                controlled_threading.cancel_all_greenlets()


        finally:
            storage.execution_history.pop()


def main():
    if len(sys.argv) < 2:
        sys.exit("missing argument specifying file to be tested")

    run_storage = RunStorage()
    run_storage.file_being_run = sys.argv[1]
    
    try:
        for i in xrange(100):
            print "Running with context switch bound of %i" % i
            run_interleavings(i, 10, run_storage)
            if run_storage.fail_paths:
                break
            print
    except KeyboardInterrupt:
        print "Run interrupted by user"

    if run_storage.fail_paths:
        shortest_fail = run_storage.fail_paths[0]
        for fail_path in run_storage.fail_paths:
            if len(fail_path) < len(shortest_fail):
                shortest_fail = fail_path
                
        print "Shortest failure path: %s" % shortest_fail
        
    else:
        print "No test failures detected"


if __name__ == '__main__':
    main()
