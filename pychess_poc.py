import sys
import controlled_threading

# install controlled_threading in sys.modules so future imports get this module 
#    Note to pydev users: add a breakpoint on the following line to make all 
#    your troubles go away (haven't investigated why this works, but it does)
sys.modules['threading'] = controlled_threading

filename = 'bank_transaction.py'
execution_path = []
greenlet_list = controlled_threading.get_greenlet_list()
shortest_fail = None


def run_step(max_depth):
    if not controlled_threading.are_greenlets_alive():
        print "%s: all greenlets completed" % execution_path
        return
    
    if max_depth is 0:
        print "%s: depth bound reached, proceeding with next path" % execution_path
        return

    for stepIndex in xrange(len(greenlet_list)): # use indices since greenlet_list will change each iteration
        greenlet = greenlet_list[stepIndex]
        if greenlet:
            execution_path.append(stepIndex)
            try:
                greenlet.switch()
                run_step(max_depth-1)
            except AssertionError, e:
                global shortest_fail
                if not shortest_fail or len(execution_path) < len(shortest_fail):
                    shortest_fail = execution_path[:] # make a copy... we want to hold on to this
                print "%s: test failure (%s) with" % (execution_path, e)

            execution_path.pop()
            controlled_threading.restart_and_replay(filename, execution_path)
        
        else:
            print "%s: skipping (greenlet %s already dead)" % (execution_path + [stepIndex, ], stepIndex)


def main():
    controlled_threading.start_main_greenlet_from_file(filename)
    run_step(10)

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
