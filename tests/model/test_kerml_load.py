from pathlib import Path
from uuid import uuid4

import pytest

from pymbe.model import Element, Model


def test_classifier_load(basic_load_files):

    level1 = basic_load_files["Level1"]
    level2 = basic_load_files["Level2"]
    level3 = basic_load_files["Level3"]

    level1_classes = [classifier for classifier in list(level1.elements.values()) if classifier._metatype == 'Classifier']
    
    # Level 1 check
    # find My Bare Class
    # find My Class with Two features
    # find Class with Typed Features
    # find Specialized Class

    assert "My Bare Class" in [classifier.declaredName for classifier in level1_classes]

    # Level 2 check
    # find Context

    level2_classes = [classifier for classifier in list(level2.elements.values()) if classifier._metatype == 'Classifier']

    assert "Context" in [classifier.declaredName for classifier in level2_classes]

    # Level 3 check
    # find Adding Machine

    level3_classes = [classifier for classifier in list(level2.elements.values()) if classifier._metatype == 'Classifier']

    assert "Adding Machine" in [classifier.declaredName for classifier in level3_classes]

    assert True

def test_feature_load(basic_load_files):

    # Level 1 check
    # find Test Feature 1
    # find Test Feature 2
    # find Bare Feature
    # find Bare Classed Feature
    # find Typed Feature 1
    # find Typed Feature 2

    # Level 2 check
    # find Side 1
    # find two 'Value' features
    # find Side 2

    # Level 3 check
    # find Register 1
    # find Register 2
    # find Register 3
    

    assert True
