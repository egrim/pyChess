import sys
import optparse

import controlled_threading

VERSION_STRING = "v0.1 (prerelease)"

DEFAULT_DEPTH_LIMIT = 10


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
        
        self.file_being_run = None
        self.last_greenlet_run = None
        self.new_path_run = False
    

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
                storage.new_path_run = True
                print "%s: test failure (%s)" % (storage.execution_history, e)
                continue
            else:
                if not controlled_threading.are_greenlets_alive():
                    storage.complete_paths.append(storage.execution_history[:])
                    storage.new_path_run = True
                    print "%s: finished (all greenlets completed)" % storage.execution_history
                    continue
                
                if max_depth <= 1:
                    storage.depth_limited_paths.append(storage.execution_history[:])
                    storage.new_path_run = True
                    print "%s: aborting (depth limit reached)" % storage.execution_history
                    continue
                
                run_interleavings(switches_left, max_depth - 1, storage)

            finally:
                controlled_threading.cancel_all_greenlets()


        finally:
            storage.execution_history.pop()


def main():
    parser = optparse.OptionParser(usage="%prog [options] PROGRAM_TO_TEST", version="%prog " + VERSION_STRING)
    parser.add_option("-c", "--startContextDepth", dest="startContextDepth", type="int", default=0, help="specify a context depth at which to start iterative context bounding (defaults to %default)")
    parser.add_option("-m", "--maxContextDepth", dest="maxContextDepth", type="int", default=sys.maxint, help="specify a maximum context depth for iterative context bounding")
    parser.add_option("-d", "--depth", dest="depth", type="int", default=DEFAULT_DEPTH_LIMIT, help="specify the maximum run depth (defaults to %default)")
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose", default=True, help="don't print status message to stdout (not yet implemented)")
    
    (options, arguments) = parser.parse_args()
    
    if not arguments:
        parser.error("missing argument specifying file to be tested")

    run_storage = RunStorage()
    run_storage.file_being_run = arguments[0]
    
    try:
        for i in xrange(options.startContextDepth, min(sys.maxint, options.maxContextDepth+1)):
            run_storage.new_path_run = False
            print "Running with context switch bound of %i" % i
            run_interleavings(i, options.depth, run_storage)
            if run_storage.fail_paths:
                print "Test failure detected with this context switch bound, discontinuing search"
                break
            
            if run_storage.new_path_run is False:
                print "No new interleavings run with this context switch bound, search complete"
                break
            
            print
    except KeyboardInterrupt:
        print "Run interrupted by user, discontinuing search"

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
