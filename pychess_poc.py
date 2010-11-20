import sys
import controlled_threading

# install controlled_threading in sys.modules so future imports get this module 
#    Note to pydev users: add a breakpoint on the following line to make all 
#    your troubles go away (haven't investigated why this works, but it does)
sys.modules['threading'] = controlled_threading

execution_path = []
greenlet_list = controlled_threading.get_greenlet_list()
shortest_fail = None


def run_interleavings(switches, depth, last_greenlet_run):
    if not controlled_threading.are_greenlets_alive():
        print "%s: finished (all greenlets completed)" % execution_path
        return

    if depth is 0:
        print "%s: aborting (depth bound reached)" % execution_path
        return

    for stepIndex in xrange(len(greenlet_list)): # use indices since greenlet_list will change each iteration
        greenlet = greenlet_list[stepIndex]
        if not greenlet:
            print "%s: skipping (greenlet %s already completed)" % (execution_path + [stepIndex, ], stepIndex)
            continue

        execution_path.append(stepIndex)
        try:
            if greenlet != last_greenlet_run:
                if switches is 0:
                    print "%s: skipping (context bound reached)" % execution_path
                    continue
                switches_left = switches - 1
            else:
                switches_left = switches

            try:            
                last_greenlet_run = greenlet.switch()
                run_interleavings(switches_left, depth - 1, last_greenlet_run)
            except AssertionError, e:
                global shortest_fail
                if not shortest_fail or len(execution_path) < len(shortest_fail):
                    shortest_fail = execution_path[:] # make a copy... we want to hold on to this
                print "%s: test failure (%s)" % (execution_path, e)
        finally:
            execution_path.pop()

        controlled_threading.start_greenlet_from_file(sys.argv[1], execution_path)


def main():
    if len(sys.argv) < 2:
        sys.exit("missing argument specifying file to be tested")

    last_greenlet_run = controlled_threading.start_greenlet_from_file(sys.argv[1])
    run_interleavings(5, 10, last_greenlet_run)

    if shortest_fail:
        print "Shortest failure path: %s" % shortest_fail

#        for step in execution_path[:-1]:
#            greenlet_list.switch()
#            
#        
#            
#        try:
#            next_greenlet
#        if execution_path:
#                next_index = execution_path[-1] + 1
#            else:
#                next_index = 0
#                
#            live_greenlets = [greenlet for greenlet in greenlet_list[next_index:] if greenlet]
#            if live_greenlets:
#                next_switch = live_greenlets[0]
#                execution_path.append(next_index)
#                next_switch.switch()
#            else:
#                execution_path.pop()
#                break

    print 'done'


if __name__ == '__main__':
    main()
