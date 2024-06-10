import json
import pymbe.api as pm

import copy

from importlib import resources as lib_resources

from pathlib import Path

from typing import Any, Collection, Dict, List, Tuple, Union

from pymbe.model import Model, Element
from pymbe.model_modification import *

from pymbe.query.metamodel_navigator import (is_type_undefined_mult,
                                    is_multiplicity_one,
                                    is_multiplicity_specific_finite,
                                    get_finite_multiplicity_types,
                                    identify_connectors_one_side,
                                    get_lower_multiplicity,
                                    get_upper_multiplicity,
                                    does_behavior_have_write_features,
                                    get_most_specific_feature_type,
                                    has_type_named,
                                    get_effective_lower_multiplicity,
                                    get_effective_basic_name,
                                    get_feature_bound_values,
                                    get_more_general_types)

from pymbe.metamodel import (derive_inherited_featurememberships,
                             classifier_metas,
                             feature_metas,
                             assoc_metas,
                             connector_metas,
                             datatype_metas
)

from pymbe.interpretation.occurrences_steps import is_feature_involving_self
from pymbe.interpretation.working_maps import FeatureTypeWorkingMap

from uuid import uuid4

class KermlForwardExecutor():
    """
    An execution class that applies the methods from the draft KerML Annex A for execution.
    """

    _working_map = None
    _working_package = None

    def __init__(self, model, target_package):
        self._working_map = FeatureTypeWorkingMap(model=model)
        self._working_package = target_package

    def execute_from_classifier(self, classifier: Element):
        """
        Run the executor on the classifier provided as an argument
        """

        self._generate_values_for_features_in_type(
            input_model=self._working_map._model,
            package_to_populate=self._working_package,
            type_to_value=classifier,
            atom_index=0)
        
        self._working_map.cover_features_in_new_atoms(self._working_package)

    def _generate_values_for_features_in_type(self,
                                              input_model,
                                              package_to_populate,
                                              type_to_value,
                                              atom_index):
        
        """
        Inspect the type and determine what values should be applied to its Features.
        """
        
        print(f"Applying Annex A atom algorithm to {type_to_value.basic_name}")
    
        new_classifier = None
        
        # TODO: Create map from new_classifier to the features discovered under this type rather than having the dictionary key to features globally
        
        if type_to_value._metatype in classifier_metas() and not has_type_named(type_to_value, "FeatureWritePerformance"):
        
            # Step 1 - create new atom from the classifier
            base_name = type_to_value.basic_name
            new_classifier = build_from_classifier_pattern(
                owner=package_to_populate,
                name=f"My{base_name}",
                model=input_model,
                specific_fields={},
                metatype=type_to_value._metatype,
                superclasses=[type_to_value]
            )

            self._working_map._add_type_instance_to_map(new_classifier)
            
            print(f"Executing step 1. Working from {base_name} to create {new_classifier}")
        
        # use derived property 'feature' to get all features including the inherited ones
        candidate_features = type_to_value.feature
        
        try:
            #print(f"Trying to find metatype for {type_to_value.throughFeatureTyping}")
            featured_meta = type_to_value.throughFeatureTyping[0]._metatype
            print(f"Type {type_to_value.basic_name} is has a type of metatype {featured_meta}.")
            if featured_meta in datatype_metas():
                print(f"Type {type_to_value.basic_name} is typed by a datatype. Bypassing further elaboration.")
                return None
        except:
            pass
        
        print(f"...Found features {candidate_features} under the type to value {type_to_value.basic_name}.")
        
        # set up for multiple passes on the feature list, will test per pass to determine whether to handle it
        
        # TODO: Instead of this testing approach, gather all features and allocated into sub-collections that
        # handle these passes
        
        passes = ['Non-connector Features', 'FeatureWritePerformances', 'Connector Features']
        
        for pass_number, pass_kind in enumerate(passes):
            
            print(f"Currently on pass {pass_kind} under {type_to_value}.")
            print(f"Current values dict at this step is")
            print(f"{self._working_map}")
        
            for cf in candidate_features:
                
                eval_feature, lower_mult, values_set_in_model = self._common_preprocess(
                    pass_kind=pass_kind,
                    type_instance=new_classifier,
                    candidate_feature=cf
                )

                if not eval_feature:
                    continue
                
                # Pass-specific core steps
                
                if has_type_named(cf, "FeatureWritePerformance"):
                    pass # refer to create_feature_write_performance_atoms
                
                elif cf._metatype not in connector_metas() and pass_kind == 'Non-connector Features':

                    self._process_nonconnector_features(
                        type_instance=new_classifier,
                        candidate_feature=cf,
                        feature_multiplicity=lower_mult,
                        values_set_in_model=values_set_in_model,
                    )

                if cf._metatype in connector_metas() and pass_kind == 'Connector Features':
                    pass # refer to _process_connector_features
            
        if type_to_value._metatype in datatype_metas():
            print(f"Classifier {type_to_value.basic_name} is a datatype. Bypassing further elaboration.")
            return None
        
        elif get_most_specific_feature_type(type_to_value) is not None:
            
            try:
                if get_most_specific_feature_type(type_to_value)._metatype in datatype_metas():
                    print(f"Classifier {type_to_value.basic_name} is a datatype or typed by one. Bypassing further elaboration.")
                    return None
            except:
                pass
                
        print(f"Current values dict is")
        print(str(self._working_map))
        
        return None
    
    def _common_preprocess(
            self,
            pass_kind:str,
            type_instance:Element,
            candidate_feature:Element
        ):

        if has_type_named(candidate_feature, "FeatureWritePerformance") and not pass_kind == 'FeatureWritePerformances':
            return (False, None, None)
        if candidate_feature._metatype not in connector_metas() and not pass_kind == 'Non-connector Features':
            if not has_type_named(candidate_feature, "FeatureWritePerformance"):
                return (False, None, None)
        if candidate_feature._metatype in connector_metas() and not pass_kind == 'Connector Features':
            return (False, None, None)
        if get_effective_basic_name(candidate_feature) == "self":
            print(f"Adding value for self to featuring type {type_instance}")
            self._working_map._add_atom_value_to_feature(type_instance,
                                                        [candidate_feature],
                                                        type_instance)
        
        # common pre-processing steps
        
        cf_name = get_effective_basic_name(candidate_feature)
        
        lower_mult = get_effective_lower_multiplicity(candidate_feature)
        
        if lower_mult > -1:
            # need to test multiplicity
            print(f"...Found effective lower multiplicity of {cf_name} ({candidate_feature._id}) as {lower_mult}.")
        elif candidate_feature._metatype not in connector_metas():
            print(f"...{cf_name} ({candidate_feature._id}) has unbounded multiplicity. Skipping.")
            return (False, None, None)
        
        redefining_features = set(candidate_feature.reverseRedefinition)
        cf_redefined = False
        
        for rf in redefining_features:
            print(f"...Discovered that {candidate_feature} ({candidate_feature._id}) is redefined by {rf} ({rf._id})! Skipping.")
            cf_redefined = True
            
        if cf_redefined:
            return (False, None, None)
        
        # Step 2 - find Features with lower multiplicity > 0 that are not connectors
        
        # Look for existing values for the feature or previous atom assignment
        
        values_set_in_model = self._find_model_existing_values_for_feature(type_instance, [candidate_feature])

        # return True for having a Feature to further interpret
        return (True, lower_mult, values_set_in_model)
        

    def _process_feature_write_performances():

        pass

    def _process_nonconnector_features(
                self,
                type_instance:Element,
                candidate_feature:Element,
                feature_multiplicity:int,
                values_set_in_model:List[Element]
            ):

        handled_as_self_reference = is_feature_involving_self(candidate_feature)

        cf_name = get_effective_basic_name(candidate_feature)
                    
        if len(values_set_in_model) == 0 and handled_as_self_reference == False:
            # Step 3 - create new Atoms to go with the Features
            
            used_typ = get_most_specific_feature_type(candidate_feature)
            
            if used_typ._metatype in datatype_metas():
                print(f"Executing step 2. Identified {cf_name} ({candidate_feature._id}) " + \
                      f"as a non-connector Feature. No existing values found. " + \
                        f"This is a datatype. Skipping generation of values.")
                return None
            else:
                print(f"Executing step 2. Identified {cf_name} ({candidate_feature._id}) as a non-connector Feature. No existing values found. " + \
                    f"Generating {feature_multiplicity} new values specializing type {used_typ}.")
            
            for i in range(0, feature_multiplicity):
                self._inspect_feature_for_values(self._working_map._model,
                        self._working_package,
                        type_instance,
                        i,
                        candidate_feature
                    )
                
        return None

    def _process_connector_features():

        pass

    def _common_postprocess():

        pass

    def _inspect_feature_for_values(self,
                                     input_model : Model,
                                     package_to_populate : Element,
                                     featuring_type : Element,
                                     atom_index : int,
                                     cf : Element):
        
        considered_type = get_most_specific_feature_type(cf)
    
        new_ft_classifier = None
        
        type_name = "None"
        if considered_type is not None:
            type_name = considered_type.basic_name
            
        if has_type_named(cf, "Life"):
            print("Need to implement a method to generate Life values for Occurrences.")
            return {}
            
        cf_name = cf.basic_name
        
        lower_features = cf.feature
        
        #if cf._id not in values_dict_passed:
            
        new_ft_classifier = build_from_classifier_pattern(
            owner=package_to_populate,
            name=f"My{type_name}{atom_index + 1}",
            model=input_model,
            specific_fields={},
            metatype=considered_type._metatype,
            superclasses=[considered_type]
        )

        print(f"Executing step 3a. Creating atom #{atom_index + 1} to be value for {cf}" + \
              f" under {featuring_type} and specializing {considered_type}")
        
        self._working_map._add_atom_value_to_feature(featuring_type, [cf], new_ft_classifier)
        
        #apply this to the redefined properties also
        
        for redef in cf.throughRedefinition:
            print(f"Found redefined feature for {cf_name}.")
            self._working_map._add_atom_value_to_feature(featuring_type, [redef], new_ft_classifier)
        
        if len(lower_features) == 0:
            print(f"...No lower features found for {cf}. Will finish descent here.")
        elif len(lower_features) == 1:
            # check that the feature isn't just self
            if get_effective_basic_name(lower_features[0]) == 'self':
                print(f"...Only lower feature for {cf} is self. Will finish descent here.")
                return None

        print(f"...Lower features found for {cf}. Will evaluate it value generation.")
        #for lf in lower_features:
        self._generate_values_for_features_in_type(input_model,
                                        package_to_populate,
                                        cf,
                                        atom_index)
        
        return None

    def _find_model_existing_values_for_feature(self, type_instance, feat_path):
    
        print(f"...Looking to see if {feat_path} is bound to other feature values")
        
        values_in_dict = []
        feature_values_shared = False

        feat = feat_path[0]

        if len(feat_path) > 1:
            raise NotImplementedError("Nested features are not implemented yet.")
        
        print(f"...Feature values for {feat_path} are {feat.throughFeatureValue}")
        
        for bound_val in feat.throughFeatureValue:
            if bound_val._metatype == 'FeatureReferenceExpression':
                print(f"...Found a feature value bound to feature {feat}")
                referred_item = bound_val.throughMembership[0]
                feature_values_shared = True
            elif 'Literal' in bound_val._metatype:
                print(f"...Found literal value for {feat}")

        if feature_values_shared:
            print(f"...Taking values from {referred_item} to match to values set for {feat} ({feat._id})")
            try:
                values_in_dict = self._working_map._get_atom_values_for_feature(type_instance, [referred_item])
                values_in_local_dict = self._working_map._get_atom_values_for_feature(type_instance, feat_path)
                print(f"...Found values {values_in_dict} to match to values set for {feat} ({feat._id})")
                try:
                    self._working_map._add_atom_value_to_feature(
                        type_instance=type_instance,
                        feature_nesting=feat_path,
                        atom_value=values_in_local_dict + values_in_dict
                        )
                except KeyError:
                    pass
            except KeyError:
                pass
            
            #apply this to the redefined properties also
        
            for redef in feat.throughRedefinition:
                print(f"Found redefined feature for {feat}.")
                try:
                    values_in_dict = self._working_map._get_atom_values_for_feature(type_instance, [referred_item])
                    values_in_local_dict = self._working_map._get_atom_values_for_feature(type_instance, [redef])
                    print(f"...Found values {values_in_dict} to match to values set for {feat} ({feat._id})")
                    try:
                        self._working_map._add_atom_value_to_feature(
                            type_instance=type_instance,
                            feature_nesting=[redef],
                            atom_value=values_in_local_dict + values_in_dict
                            )
                    except KeyError:
                        pass
                except KeyError:
                    pass
            
            # also apply the value to redefined properties
                    
        return values_in_dict