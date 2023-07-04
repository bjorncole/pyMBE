from pymbe.model_modification import *
from pymbe.query.metamodel_navigator import *

def test_feature_mult_check(basic_load_files):

    # Tests the feature multiplicity of features

    annex_a = basic_load_files["AnnexA"]

    finite_type = get_finite_multiplicity_types(annex_a)

    assert(finite_type[0].declaredName == "rollsOn")

    assert(get_lower_multiplicty(finite_type[0]) == 2)
    assert(get_upper_multiplicty(finite_type[0]) == 2)

    # The example works from Annex A A.3.3 - One-to-One Connectors


def test_classifier_special(basic_load_files):

    # Tests the production of supersetting classifiers

    annex_a = basic_load_files["AnnexA"]

    annex_a_classifiers = [
        classifier for classifier in list(annex_a.elements.values()) if classifier._metatype == "Classifier"
    ]

    annex_a_assocs = [
        assoc for assoc in list(annex_a.elements.values()) if assoc._metatype == "Association"
    ]

    classifiers_with_features = [test_classifier
        for test_classifier in annex_a_classifiers if
        'throughFeatureMembership' in test_classifier._derived]
    
    assert (classifiers_with_features[0].declaredName == 'Bicycle')

    # The example works from Annex A A.3.3 - One-to-One Connectors