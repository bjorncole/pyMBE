

class ForwardSysMLExecution():
    """
    A class to perform forward execution on a SysML model, starting from a single target element
    and creating threads of execution as it goes. The class will use time slices to record the 
    result, but also to provide a locus of execution for the next step.
    """

    def consider_next_step():
        """
        From a given timeslice, determine the next step to take, considering nesting of 
        behaviors, potential events and triggers, and also temporal dependencies.
        """