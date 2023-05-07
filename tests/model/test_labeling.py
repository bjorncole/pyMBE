import pytest

from pymbe.model import Element, Model


def test_expression_labels(basic_load_files):

    level3 = basic_load_files["Level3"]

    expected_labels = {
        "Register 1 == Register 2 + Register 3",
        "Register 2 == Register 3 + 15.0",
        "Register 1 == Register 2 + Register 3",
        "Register 1 == My Adder.Register 2 + My Adder.Register 3.Sub-Register 1.Sub-Sub-Register 2",
        "sin(Register 1 + My Adder.Register 2) == 0.707",
        "rect(Register 1, My Adder.Register 2) == 0.0",
    }

    invariant_labels = {
        invar.throughResultExpressionMembership[0].label
        for invar in level3.ownedMetatype["Invariant"]
    }

    assert not invariant_labels.symmetric_difference(expected_labels)
