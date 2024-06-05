from typing import Dict


class FeatureTypeWorkingMap:
    """
    This is a map to hold solutions in work by the interpreter that map a
    (nested) Feature to a Type under construction. This allows the solution in
    progress to be incrementally developed before commiting to creating new
    model objects to represent the solution.
    """

    _working_dict = Dict[Dict[str, str]]
