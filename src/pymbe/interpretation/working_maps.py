from typing import Dict, List, Any

from pymbe.model import Element, Model

from pymbe.query.metamodel_navigator import (
    get_effective_basic_name,
    get_effective_lower_multiplicity,
    get_effective_upper_multiplicity,
    get_most_specific_feature_type,
)

from pymbe.model_modification import (apply_covered_feature_pattern,
                                      apply_covered_connector_pattern,
                                      apply_chained_feature_assignment_pattern,
                                      assign_value_by_literal_expression)

from pymbe.metamodel import (feature_metas, connector_metas)

from dataclasses import field

class FeatureTypeWorkingMap:
    """
    This is a map to hold solutions in work by the interpreter that map a
    (nested) Feature to a Type under construction. This allows the solution in
    progress to be incrementally developed before commiting to creating new
    model objects to represent the solution.
    """

    # The working dictionary for atoms to atoms (objects)
    _working_dict: Dict[str, Dict[str, List[Element]]] = field(default_factory=dict)
    # The working dictionary for atoms to values (objects to values)
    _working_dict_data_values: Dict[str, Dict[str, List[Element]]] = field(default_factory=dict)
    _model: Model

    def __init__(self, model):
        self._working_dict = {}
        self._working_dict_data_values = {}
        self._model = model

    def _add_type_instance_to_map(self, type_instance: Element):

        """
        Add a new type to the map under which features and their more specific
        values can be mapped.
        """

        self._working_dict.update({type_instance._id: {}})
        self._working_dict_data_values.update({type_instance._id: {}})

    def _add_feature_to_type_instance(self,
                                      type_instance: Element,
                                      feature_nesting: List[Element]):

        """
        Add a feature under a type instance that is being developed
        """

        try:
            id_path = ".".join([feature._id for feature in feature_nesting])
            self._working_dict[type_instance._id].update({id_path: []})
            self._working_dict_data_values[type_instance._id].update({id_path: []})
        except KeyError:
            raise KeyError("Tried to add a feature to an atom" + \
                           "that is not in the working dictionary.")

    def _add_atom_value_to_feature(self,
                                      type_instance: Element,
                                      feature_nesting: List[Element],
                                      atom_value: Any):
        
        """
        Add a value to the map to a nested feature under the type instance
        """

        try:
            id_path = ".".join([feature._id for feature in feature_nesting])
            if isinstance(atom_value, Element):
                self._working_dict[type_instance._id][id_path].append(atom_value)
            else:
                self._working_dict_data_values[type_instance._id][id_path].append(atom_value)
        except KeyError:
            try:
                self._add_feature_to_type_instance(
                    type_instance=type_instance,
                    feature_nesting=feature_nesting)
                if isinstance(atom_value, Element):
                    self._working_dict[type_instance._id][id_path].append(atom_value)
                else:
                    self._working_dict_data_values[type_instance._id][id_path].append(atom_value)
            except KeyError:
                raise KeyError(f"Tried to add a value to a feature {feature_nesting} " + \
                           f"to an atom {type_instance} " + \
                           "that is not in the working dictionary.")
        
    def _get_atom_values_for_feature(self,
                                     type_instance: Element, 
                                     feature_nesting: List[Element]):
        
        id_path = ".".join([feature._id for feature in feature_nesting])

        try:
            return self._working_dict[type_instance._id][id_path]
        except KeyError:
            return []
        
    def __repr__(self):

        map_string = ""

        for type_instance_id in self._working_dict:
            map_string = map_string + f"Values mapped under type instance (atom) " + \
                 f"{get_effective_basic_name(self._model.get_element(type_instance_id))}:\n"
            for feature_path in self._working_dict[type_instance_id]:
                feature_rep = ".".join([str(self._model.get_element(item_id))
                                for item_id in feature_path.split(".")])
                
                map_string = map_string + f"{feature_rep} has values " + \
                    f"{self._working_dict[type_instance_id][feature_path]}\n"
                
        return "Empty" if map_string == "" else map_string
    
    def cover_features_in_new_atoms(self, target_packge):

        for type_instance_id in self._working_dict:
            
            type_instance = self._model.get_element(type_instance_id)
            bound_features_to_atom_values_dict = self._working_dict[type_instance_id]

            for bound_feature_id in bound_features_to_atom_values_dict.keys():
                if len(bound_feature_id.split(".")) > 1:
                    if len(bound_features_to_atom_values_dict[bound_feature_id]) > 0:
                        raise NotImplementedError("Connect assign values to nested features yet.")
                    else:
                        continue
                bound_feature = self._model.get_element(element_id=bound_feature_id)
                if bound_feature._metatype in feature_metas():
                    print(f"(Atom style)...Working to connect the feature {bound_feature} to generated types inside atom {type_instance} via " + \
                        f"covering pattern with values {bound_features_to_atom_values_dict[bound_feature_id]}.")
                    
                    covering_classifier_suffix = ""

                    if get_effective_basic_name(bound_feature) in ("subperformances"):
                        covering_classifier_suffix = " under " + get_effective_basic_name(type_instance)

                    redefined_bound_feature = apply_covered_feature_pattern(
                            one_member_classifiers=bound_features_to_atom_values_dict[bound_feature_id],
                            feature_to_cover=bound_feature,
                            type_to_apply_pattern_on=type_instance,
                            model=self._model,
                            new_types_owner=target_packge,
                            covering_classifier_prefix="Values for ",
                            covering_classifier_suffix=covering_classifier_suffix,
                            redefining_feature_prefix="",
                            redefining_feature_suffix=" (Covered)",
                    )
                if bound_feature._metatype in connector_metas():
                    print(f"(Atom style)...Working to connect the feature {bound_feature} to generated types inside atom {type_instance} via " + \
                        f"covering pattern with values {bound_features_to_atom_values_dict[bound_feature_id]}.")
                    print(f"...Building covered connector under {type_instance}")
                            
                    redefined_bound_feature = apply_covered_connector_pattern(
                        one_member_classifiers=bound_features_to_atom_values_dict[bound_feature_id],
                        feature_to_cover=bound_feature,
                        type_to_apply_pattern_on=type_instance,
                        model=self._model,
                        new_types_owner=target_packge,
                        covering_classifier_prefix="Values for ",
                        covering_classifier_suffix="",
                        redefining_feature_prefix="",
                        redefining_feature_suffix="",
                        metatype=bound_feature._metatype,
                        separate_connectors=True
                    )
        
        for type_instance_id in self._working_dict_data_values:
            
            type_instance = self._model.get_element(type_instance_id)
            bound_features_to_atom_values_dict = self._working_dict_data_values[type_instance_id]

            for bound_feature_id in bound_features_to_atom_values_dict.keys():
                # set the value through a feature chain and new feature
                if len(bound_feature_id.split(".")) > 1:
                    bound_feature_path = \
                        [self._model.get_element(feat_id) for feat_id in bound_feature_id.split(".")]
                    chained_feature = apply_chained_feature_assignment_pattern(
                        feature_path_to_chain=bound_feature_path,
                        type_to_apply_pattern_on=type_instance,
                        model=self._model,
                        chained_feature_prefix="",
                        chained_feature_suffix=""
                    )

                    print(f"Assigning nested feature value {bound_features_to_atom_values_dict[bound_feature_id]} to {bound_feature_path}")

                    assign_value_by_literal_expression(
                        target_feature=chained_feature,
                        value_to_assign=bound_features_to_atom_values_dict[bound_feature_id][0]
                            if len(bound_features_to_atom_values_dict[bound_feature_id]) == 1
                            else bound_features_to_atom_values_dict[bound_feature_id],
                        model=self._model
                    )
                else:
                    # set the value directly
                    pass