import random
import copy

import networkx as nx

from ..graph import SysML2LabeledPropertyGraph


def retrieve_element(elements: dict, element: (dict, str), strict: bool = True) -> dict:
    input_element = element
    if isinstance(element, str):
        element = elements.get(element, None)
    elif not isinstance(element, dict):
        raise ValueError(f"Failed to process element: '{input_element}'")
    if strict and element is None:
        raise ValueError(f"Failed to process element: '{input_element}'")
    return element


def get_metaclass(elements: dict, element: (dict, str)) -> str:
    element = retrieve_element(elements, element)
    return element.get("@type", None)


def get_feature_upper_multiplicity(
    elements: dict,
    feature: (dict, str),
) -> (None, int):
    feature = retrieve_element(elements, feature)

    multiplicity = elements.get((feature.get("multiplicity") or {}).get("@id"))
    if multiplicity is None:
        return None

    upper_bound = elements.get((multiplicity.get("upperBound") or {}).get("@id"))
    if upper_bound is None:
        return None

    return upper_bound.get("value")


def make_banded_featuring_graph(lpg: SysML2LabeledPropertyGraph) -> nx.DiGraph:
    return lpg.filter(
        edge_types=(
            "FeatureMembership",
            "FeatureTyping",
            "Redefinition",
            "Superclassing",
        ),
        reverse_edge_types=(
            "FeatureMembership",
            "FeatureTyping",
        )
    )


class InstanceGenerationStrategy:
    """
    Base class for approaches to creating sets of instances conforming to a model
    """
    def __init__(self, number_of_cases=10, model_session=None, short_names=None):
        self.classifier_instance_dicts = {}
        self.feature_instance_dicts = {}

        self.no_alts = number_of_cases
        self.session = model_session
        self.short_pre_bake = short_names

    def pprint_classifier_solution(self, solution_no=0):
        for key, val in self.classifier_instance_dicts[solution_no].items():
            print(self.session.get_name_by_id(key) + ', id = ' + key + ', size = ' + str(len(val)))
            short_list = []
            for indx, ind_val in enumerate(val):
                if indx < 5:
                    short_list.append(ind_val)
            print(short_list)


    def pprint_feature_solution(self, solution_no=0):
        for key, val in self.feature_instance_dicts[solution_no].items():
            print(self.session.get_name_by_id(key) + ', id = ' + key + ', size = ' + str(len(val)))
            short_list = []
            for indx, ind_val in enumerate(val):
                if indx < 5:
                    short_list.append(ind_val)
            print(short_list)

    def pprint_attribute_solution(self, solution_no=0):
        for key, val in self.attribute_dicts[solution_no].items():
            key_data = self.session.get_data_by_id(key)
            print(self.session.get_name_by_id(key) +
                  '::' + self.session.get_name_by_id(key_data['owningType']['@id']) +
                  ', id = ' + key + ', size = ' + str(len(val)))
            short_list = []
            for indx, ind_val in enumerate(val):
                if indx < 5:
                    short_list.append(ind_val)
            print(short_list)


class RandomGenerationStrategy(InstanceGenerationStrategy):
    """
    Generate instances at random based on a model
    """
    def __init__(self, number_of_cases=10, model_session=None, short_names=None):
        """
        Execute the instance space generator from the constructor
        :param number_of_cases: number of alternative solutions to generate
        :param model_session: handle to live session of model data
        """
        super().__init__(number_of_cases=number_of_cases, model_session=model_session, short_names=short_names)

        # break down abstract classifiers into more specific bins
        self.partitioned_multiplicity_dicts = self.build_partitioned_multiplicities()
        # pre-calculate nesting of features
        self.sequence_templates = self.build_sequence_templates()
        # build out classifier sets
        self.classifier_instance_dicts = self.generate_classifier_populations()
        #self.pprint_classifier_solution(solution_no=1)
        # try to "roll up" instances - apparently we can simply repeat this until all nodes have been touched
        # note that the same approach works for solving expression trees (work from leaves to nodes)
        safety = 0
        while self.push_classifiers_more_general() > 0 and safety < 100:
            safety = safety + 1
        self.populate_standalone_non_abstract_classifiers()
        #self.pprint_classifier_solution(solution_no=1)
        self.feature_instance_dicts = self.generate_feature_populations()

        self.redefinition_sequences = self.build_redefinition_sequences()

        self.attribute_dicts = self.generate_value_holders()

    def build_partitioned_multiplicities(self):
        """
        Calculate how the different instances of an abstract classifier should be sub-divided
        :return: dictionary of classifier, either direct to number or a sub-dictionary pointing to sub-division
        """

        # TODO: Flatten the dictionary to cover only abstract sub-sets

        partitioned_multiplicity_dicts = []
        upper_mults = self.session.graph_manager.roll_up_upper_multiplicities()
        abstract_map = {}

        for um in upper_mults:
            if self.session.get_metaclass_by_id(um) == 'PartUsage':
                types = list(self.session.graph_manager.feature_typing_graph.successors(um))
                if len(types) == 1:
                    if self.session.get_data_by_id(types[0])['isAbstract']:
                        abstracts = self.session.graph_manager.partition_abstract_type(abstract_type_id=types[0])
                        abstract_map.update({um: abstracts})
                else:
                    pass
            elif self.session.get_metaclass_by_id(um) == 'PartDefinition':
                if self.session.get_data_by_id(um)['isAbstract']:
                    abstracts = self.session.graph_manager.partition_abstract_type(abstract_type_id=um)
                    abstract_map.update({um: abstracts})

        for step in range(0, self.no_alts):

            partitioned_multiplicity_dict = {}

            # iterate on the abstract classifiers
            for key, values in abstract_map.items():
                types = list(self.session.graph_manager.feature_typing_graph.successors(key))
                if len(types) == 1:
                    no_splits = len(values)
                    taken = 0
                    local_partition = {}
                    # iterate on the specific classifiers
                    for indx, val in enumerate(values):
                        if indx < no_splits - 1:
                            draw = random.randint(0, upper_mults[key])
                            taken = taken + draw
                        else:
                            draw = upper_mults[key] - taken
                        local_partition.update({val: draw})
                    partitioned_multiplicity_dict.update({types[0]: local_partition})

            partitioned_multiplicity_dicts.append(partitioned_multiplicity_dict)

        return partitioned_multiplicity_dicts

    def build_sequence_templates(self):
        sorted_feature_groups = []
        for comp in nx.connected_components(self.session.graph_manager.part_featuring_graph.to_undirected()):
            connected_sub = nx.subgraph(self.session.graph_manager.part_featuring_graph, list(comp))
            sorted_feature_groups.append(
                [node for node in nx.topological_sort(connected_sub)]
            )

        return sorted_feature_groups

    def build_redefinition_sequences(self):
        sorted_redefinition_groups = []

        for comp in nx.connected_components(self.session.graph_manager.redefinition_graph.to_undirected()):
            connected_sub = nx.subgraph(self.session.graph_manager.redefinition_graph, list(comp))
            sorted_redefinition_groups.append(
                [node for node in nx.topological_sort(connected_sub)]
            )

        return sorted_redefinition_groups

    def generate_classifier_populations(self):
        classifier_instance_dicts = []
        upper_mults = self.session.graph_manager.roll_up_upper_multiplicities()

        for step in range(0, self.no_alts):

            classifier_instance_dict = {}
            # work with the abstract break-outs
            partitioned_abstract = self.partitioned_multiplicity_dicts[step]
            for key, val in partitioned_abstract.items():
                for specific_key, mult in val.items():
                    instances_list = []
                    instances_number = (partitioned_abstract[key][specific_key] + 1)
                    for index in range(1, instances_number):
                        new_instance = Instance(
                            self.session.get_name_by_id(specific_key),
                            index,
                            self.short_pre_bake
                        )
                        instances_list.append(new_instance)
                    classifier_instance_dict.update({specific_key: instances_list})

            # work with non-abstract classifiers
            for key, mult in upper_mults.items():
                types = list(self.session.graph_manager.feature_typing_graph.successors(key))
                # check that we haven't already add the keys to the list (for abstract types)
                if len(types) == 1 and types[0] not in self.partitioned_multiplicity_dicts[0]:
                    instances_list = []
                    instances_number = (mult + 1)
                    for index in range(1, instances_number):
                        new_instance = Instance(
                            self.session.get_name_by_id(types[0]),
                            index,
                            self.short_pre_bake
                        )
                        instances_list.append(new_instance)
                    classifier_instance_dict.update({types[0]: instances_list})

            classifier_instance_dicts.append(classifier_instance_dict)

        return classifier_instance_dicts

    def push_classifiers_more_general(self):
        """
        Take specific classifiers and push the calculated instances to more general classifiers
        :return:
        """
        white_list = []

        for classifier_instance_dict in self.classifier_instance_dicts:
            white_list = list(self.session.graph_manager.superclassing_graph.nodes())
            black_list = list(classifier_instance_dict.keys())
            for black in black_list:
                white_list.remove(black)
            root_drop = []
            for white in white_list:
                # try to pull out items with no incoming links
                if self.session.graph_manager.superclassing_graph.in_degree(white) == 0:
                    classifier_instance_dict.update({white: []})
                    root_drop.append(white)
            for rd in root_drop:
                black_list.append(rd)
                white_list.remove(rd)

            first_pass_dict = {}

            # try to cover all white list nodes with inputs from black-listed nodes, first pass is pulling data
            # from classifier_instance_dict as is

            for key in classifier_instance_dict:
                for gen in self.session.graph_manager.superclassing_graph.successors(key):
                    # bail if we've already been here
                    if gen in black_list:
                        break
                    gen_covered = True
                    instance_working_list = []
                    for re_spec in self.session.graph_manager.superclassing_graph.predecessors(gen):
                        if re_spec in classifier_instance_dict:
                            instance_working_list.extend(classifier_instance_dict[re_spec])
                        if re_spec in white_list:
                            gen_covered = False
                            break
                    if gen_covered:
                        #if the current node is white and all predecessors are black, then can roll instances up
                        first_pass_dict.update({gen: instance_working_list})
                        white_list.remove(gen)
                        black_list.append(gen)

            classifier_instance_dict.update(first_pass_dict)

        return len(white_list)

    def populate_standalone_non_abstract_classifiers(self):
        """
        Cover the case where a PartDefinition types nothing and is non-abstract - should create one instance
        :return:
        """
        on_superclass_graph = list(self.session.graph_manager.superclassing_graph.nodes())
        all_part_defs = self.session.get_all_of_metaclass("PartDefinition")

        all_part_def_ids = []

        for part_def in all_part_defs:
            all_part_def_ids.append(part_def['@id'])

        for on_graph in on_superclass_graph:
            if on_graph in all_part_defs:
                all_part_def_ids.remove(on_graph)

        for classifier_instance_dict in self.classifier_instance_dicts:
            for all_part_id in all_part_def_ids:
                if all_part_id not in list(classifier_instance_dict.keys()):
                    new_instance = Instance(
                        self.session.get_name_by_id(all_part_id),
                        1,
                        self.short_pre_bake
                    )
                    classifier_instance_dict.update({all_part_id: [new_instance]})

    def generate_feature_populations(self):
        feature_sequence_dictionaries = []
        feature_mult_dictionary = self.session.graph_manager.roll_up_upper_multiplicities()

        for step in range(0, self.no_alts):

            classifier_instance_dict = self.classifier_instance_dicts[step]

            feature_sequence_dictionary = {}
            covered_draw_dict = {}

            for sorting in self.sequence_templates:
                for indx, node in enumerate(sorting):
                    if indx > 0:
                        new_dict = {}
                        # get current parent from the graph
                        for pred in self.session.graph_manager.part_featuring_graph.predecessors(node):
                            current_parent = pred
                            # print(working_model.get_name_by_id(current_parent))

                        sequence_of_sequences = []

                        for sequence in feature_sequence_dictionary[current_parent]:

                            test_mult = random.randint(
                                self.session.feature_lower_multiplicity(node),
                                self.session.feature_upper_multiplicity(node)
                            )

                            for ind_j in range(0, test_mult):
                                new_sequence = copy.deepcopy(sequence)
                                # find the type of the current feature node
                                node_type = self.session.graph_manager.get_feature_type(node)[0]

                                need_draw = True

                                safety_count = 0

                                while (need_draw and safety_count < 100):

                                    draw = random.randint(
                                        0,
                                        feature_mult_dictionary[node] - 1
                                    )
                                    # print((node_type, draw))
                                    # print(classifier_instance_dict[node_type][draw])

                                    if node_type in covered_draw_dict:
                                        if classifier_instance_dict[node_type][draw] in covered_draw_dict[node_type]:
                                            pass
                                            # need_draw = False
                                        else:
                                            covered_draw_dict[node_type].append(
                                                classifier_instance_dict[node_type][draw])
                                            need_draw = False
                                    else:
                                        covered_draw_dict.update(
                                            {node_type: [classifier_instance_dict[node_type][draw]]})
                                        need_draw = False

                                    safety_count = safety_count + 1
                                    if safety_count == 99:
                                        print('Safety count hit when trying to place ' +
                                              str(classifier_instance_dict[node_type][draw]) + ' under ' +
                                              str(new_sequence))
                                        print('Covered dict is ' + str(covered_draw_dict[node_type]))

                                new_sequence.append(classifier_instance_dict[node_type][draw])

                                sequence_of_sequences.append(new_sequence)

                        feature_sequence_dictionary.update({node: sequence_of_sequences})

                    elif indx == 0:
                        if isinstance(classifier_instance_dict[node], list):
                            starter_list = []
                            for item in classifier_instance_dict[node]:
                                starter_list.append([item])
                            # handle case where main type has more than one instance
                            feature_sequence_dictionary.update({node: starter_list})
                            # print(starter_list)
                            if len(starter_list) == 0:
                                break
                        else:
                            feature_sequence_dictionary.update({node: [[classifier_instance_dict[node]]]})

            feature_sequence_dictionaries.append(feature_sequence_dictionary)

        return feature_sequence_dictionaries

    def generate_value_holders(self):

        attribute_dictionaries = []

        full_attribute_list = [att['@id'] for att in self.session.get_all_of_metaclass(metaclass_name="AttributeUsage")]

        for indx, classifier_instance_dict in enumerate(self.classifier_instance_dicts):
            attribute_dictionaries.append({})

        for redef_seq in self.redefinition_sequences:
            for att in redef_seq:
                full_attribute_list.remove(att)
                att_data = self.session.get_data_by_id(att)
                att_owner_id = att_data['owningType']['@id']
                att_owner = self.session.get_data_by_id(att_owner_id)
                print(att_data['name'] + ' is under ' + att_owner['name'])

                for indx, classifier_instance_dict in enumerate(self.classifier_instance_dicts):
                    new_holders = []
                    if att_owner_id in classifier_instance_dict:
                        #print('Found attribute owner in classifier dict')
                        for instance in classifier_instance_dict[att_owner_id]:
                            if isinstance(instance, list):
                                preseq = copy.deepcopy(instance)
                            else:
                                preseq = [instance]
                            #print(instance)
                            new_holder = ValueHolder([instance], att_data['name'], None, att)
                            preseq.append(new_holder)
                            new_holders.append(preseq)

                    elif att_owner_id in self.feature_instance_dicts[indx]:
                        #print('Found attribute owner in feature dict')
                        for instance_seq in self.feature_instance_dicts[indx][att_owner_id]:
                            preseq = copy.deepcopy(instance_seq)
                            #print(instance_seq)
                            new_holder = ValueHolder(instance_seq, att_data['name'], None, att)
                            preseq.append(new_holder)
                            new_holders.append(preseq)

                    attribute_dictionaries[indx].update({att: new_holders})

        for att_id in full_attribute_list:
            att_data = self.session.get_data_by_id(att_id)
            att_owner_id = att_data['owningType']['@id']
            for indx, classifier_instance_dict in enumerate(self.classifier_instance_dicts):
                new_holders = []
                if att_owner_id in classifier_instance_dict:
                    # print('Found attribute owner in classifier dict')
                    for instance in classifier_instance_dict[att_owner_id]:
                        if isinstance(instance, list):
                            preseq = copy.deepcopy(instance)
                        else:
                            preseq = [instance]
                        # print(instance)
                        new_holder = ValueHolder([instance], att_data['name'], None, att_id)
                        preseq.append(new_holder)
                        new_holders.append(preseq)

                elif att_owner_id in self.feature_instance_dicts[indx]:
                    # print('Found attribute owner in feature dict')
                    for instance_seq in self.feature_instance_dicts[indx][att_owner_id]:
                        preseq = copy.deepcopy(instance_seq)
                        # print(instance_seq)
                        new_holder = ValueHolder(instance_seq, att_data['name'], None, att_id)
                        preseq.append(new_holder)
                        new_holders.append(preseq)

                attribute_dictionaries[indx].update({att_id: new_holders})

        return attribute_dictionaries

class Instance:
    """
    A class to represent instances of real things in the M0 universe interpreted from the model.
    Sequences of instances are intended to follow the mathematical base semantics of SysML v2.
    """
    def __init__(self, name, index, pre_bake):
        self.name = shorten_name(name, shorten_pre_bake=pre_bake) + '#' + str(index)

    def __repr__(self):
        return self.name


class ValueHolder:
    """
    A class to represent instances of the attribution of real things in the M0 universe interpreted from the model.
    Sequences of instances and value holders are intended to follow the mathematical base semantics of SysML v2.
    Additionally, the value holders are meant to be variables in numerical analyses.
    """
    def __init__(self, path, name, value, base_att):
        # path is list of instance references
        self.holder_string = ''
        for indx, step in enumerate(path):
            if indx == 0:
                self.holder_string = str(step)
            else:
                self.holder_string = self.holder_string + '.' + str(step)
        self.holder_string = self.holder_string + '.' + name
        self.value = value
        self.base_att = base_att

    def __repr__(self):
        if self.value is not None:
            return self.holder_string + ' (' + str(self.value) + ')'
        else:
            return self.holder_string + ' (unset)'


def shorten_name(name, shorten_pre_bake=None):
    """
    Helper to get short names for reporting many instances
    :param name: Existing name to shorten
    :param shorten_pre_bake: A pre-computed dictionary mapping long names to custom short names
    :return: a shortened version of the input name if the input is longer than five characters
    """
    short_name = ''
    if len(name) > 5:
        if shorten_pre_bake is not None:
            if name in shorten_pre_bake:
                return shorten_pre_bake[name]
        space_place = name.find(' ')
        if space_place > -1:
            short_name = short_name + name[0]
            short_name = short_name + name[space_place + 1]
            next_space = name.find(' ', space_place + 1)
            while next_space > -1:
                short_name = short_name + name[next_space + 1]
                next_space = name.find(' ', next_space + 1)
            return short_name
    return name
