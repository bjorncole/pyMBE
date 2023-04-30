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

    level3_classes = [classifier for classifier in list(level3.elements.values()) if classifier._metatype == 'Classifier']

    assert "Adding Machine" in [classifier.declaredName for classifier in level3_classes]

def test_feature_load(basic_load_files):

    level1 = basic_load_files["Level1"]
    level2 = basic_load_files["Level2"]
    level3 = basic_load_files["Level3"]

    # Level 1 check

    level1_features = [feature for feature in list(level1.elements.values()) if feature._metatype == 'Feature']

    # find Test Feature 1
    assert "Test Feature 1" in [feature.declaredName for feature in level1_features if hasattr(feature, "declaredName")]
    # find Test Feature 2
    assert "Test Feature 2" in [feature.declaredName for feature in level1_features if hasattr(feature, "declaredName")]
    # find Bare Feature
    assert "Bare Feature" in [feature.declaredName for feature in level1_features if hasattr(feature, "declaredName")]
    # find Bare Classed Feature
    assert "Bare Classed Feature" in [feature.declaredName for feature in level1_features if hasattr(feature, "declaredName")]
    # find Typed Feature 1
    assert "Typed Feature 1" in [feature.declaredName for feature in level1_features if hasattr(feature, "declaredName")]
    # find Typed Feature 2
    assert "Typed Feature 2" in [feature.declaredName for feature in level1_features if hasattr(feature, "declaredName")]

    # Level 2 check
    level2_features = [feature for feature in list(level2.elements.values()) if feature._metatype == 'Feature']
    # find Side 1
    assert "Side 1" in [feature.declaredName for feature in level2_features  if hasattr(feature, "declaredName")]
    # find two 'Value' features
    assert "Value" in [feature.declaredName for feature in level2_features  if hasattr(feature, "declaredName")]
    assert len([feature for feature in level2_features
                 if hasattr(feature, "declaredName") and feature.declaredName == "Value"]) == 2
    # find Side 2
    assert "Side 2" in [feature.declaredName for feature in level2_features  if hasattr(feature, "declaredName")]

    # Level 3 check
    level3_features = [feature for feature in list(level3.elements.values()) if feature._metatype == 'Feature']
    # find Register 1
    assert "Register 1" in [feature.declaredName for feature in level3_features  if hasattr(feature, "declaredName")]
    # find Register 2
    assert "Register 2" in [feature.declaredName for feature in level3_features  if hasattr(feature, "declaredName")]
    # find Register 3
    assert "Register 3" in [feature.declaredName for feature in level3_features  if hasattr(feature, "declaredName")]
    
