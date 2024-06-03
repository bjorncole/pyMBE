import pytest

from pymbe.model import Element, Model
from pymbe.query.metamodel_navigator import (
    get_effective_basic_name,
    get_effective_lower_multiplicity,
    get_effective_upper_multiplicity,
    get_most_specific_feature_type,
)

def test_create_new_performance(load_library):

    """
    Try the creation of new classifiers that specialize library elements.

    """

    pass