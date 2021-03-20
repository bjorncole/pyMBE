import networkx as NX


class ModelingSession:
    """
    A class to contain a live, in-memory version of the model and support rapid execution of commands
    """

    def __init__(self, ele_list=None):
        self.lookup = ModelLookup()
        self.ele_list = ele_list
        self.graph_manager = GraphManager(session_handle=self)

    def thaw_json_data(self, jsons=()):
        self.lookup.memoize_many(ele_list=jsons)
        self.graph_manager.build_graphs_from_data(ele_list=jsons)

    def get_data_by_id(self, ele_id=''):
        trial = self.lookup.get_element_by_id(ele_id=ele_id)
        if trial is None:
            for ele in self.ele_list:
                if ele['@id'] == id:
                    self.lookup.memoize_one(ele=ele)
                    return ele
        else:
            return trial

        raise ValueError("No element found with ID = " + str(ele_id))

    def get_name_by_id(self, ele_id=''):
        trial = self.get_data_by_id(ele_id=ele_id)
        if trial is not None and 'name' in trial:
            return trial['name']
        else:
            return None

    def get_metaclass_by_id(self, ele_id=''):
        trial = self.get_data_by_id(ele_id=ele_id)
        if trial is not None and '@type' in trial:
            return trial['@type']
        else:
            return None

    def get_all_of_metaclass(self, metaclass_name=''):
        if metaclass_name in self.lookup.metaclass_lookup:
            return [self.get_data_by_id(this_id) for this_id in self.lookup.metaclass_lookup[metaclass_name]]
        else:
            return []

    def feature_lower_multiplicity(self, feature_id=''):
        feature = self.get_data_by_id(feature_id)
        if feature['multiplicity'] is not None:
            if '@id' in feature['multiplicity']:
                mult = self.get_data_by_id(feature['multiplicity']['@id'])
                if '@id' in mult['lowerBound']:
                    return self.get_data_by_id(mult['lowerBound']['@id'])['value']

        return 1

    def feature_upper_multiplicity(self, feature_id=''):
        feature = self.get_data_by_id(feature_id)
        if feature['multiplicity'] is not None:
            if '@id' in feature['multiplicity']:
                mult = self.get_data_by_id(feature['multiplicity']['@id'])
                if '@id' in mult['upperBound']:
                    return self.get_data_by_id(mult['upperBound']['@id'])['value']

        return 1


class ModelLookup:
    """
    Support rapid return of commonly queried attributes such as name, id, and metatype
    """

    def __init__(self):
        self.id_memo_dict = {}
        self.metaclass_lookup = {}

    def memoize_many(self, ele_list=()):
        self.id_memo_dict.update({ele['@id']: ele for ele in ele_list})
        for ele in ele_list:
            if ele['@type'] in self.metaclass_lookup:
                self.metaclass_lookup[ele['@type']].append(ele['@id'])
            else:
                self.metaclass_lookup.update({ele['@type']: [ele['@id']]})


    def memoize_one(self, ele=None):
        self.id_memo_dict.update({ele['@id']: ele})
        if ele['@type'] in self.metaclass_lookup:
            self.metaclass_lookup[ele['@type']].append(ele['@id'])
        else:
            self.metaclass_lookup.update({ele['@type']: [ele['@id']]})

    def get_element_by_id(self, ele_id=''):
        if ele_id in self.id_memo_dict:
            return self.id_memo_dict[ele_id]
        else:
            return None


class KernelReference:
    """
    Utility class to hold key information about the SysML v2 language
    """


class GraphManager:
    """
    Class to handle multiple syntactic graphs to support rapid analysis of the current model
    and also semantic interpretations
    """

    def __init__(self, session_handle=None):
        self.superclassing_graph = NX.DiGraph()
        self.part_featuring_graph = NX.DiGraph()
        self.banded_featuring_graph = NX.DiGraph()
        self.session = session_handle

    def build_graphs_from_data(self, ele_list=()):
        """
        Packs elements into utility syntax graphs for later processing
        :param ele_list: list of element JSONs to pack
        :return: nothing
        """

        for ele in ele_list:
            if ele['@type'] == 'Superclassing':
                general = ele['general']['@id']
                specific = ele['specific']['@id']
                self.superclassing_graph.add_node(general, name=self.session.get_name_by_id(ele_id=general))
                self.superclassing_graph.add_node(specific, name=self.session.get_name_by_id(ele_id=specific))
                self.superclassing_graph.add_edge(general, specific)

                self.banded_featuring_graph.add_node(general, name=self.session.get_name_by_id(ele_id=general))
                self.banded_featuring_graph.add_node(specific, name=self.session.get_name_by_id(ele_id=specific))
                self.banded_featuring_graph.add_edge(general, specific, kind='Superclassing')

            elif ele['@type'] == 'FeatureTyping':
                typ = ele['type']['@id']
                feature = ele['typedFeature']['@id']

                # limit to part usages for now

                if self.session.get_metaclass_by_id(feature) == 'PartUsage':

                    self.banded_featuring_graph.add_node(feature, name=self.session.get_name_by_id(ele_id=feature))
                    self.banded_featuring_graph.add_node(typ, name=self.session.get_name_by_id(ele_id=typ))
                    self.banded_featuring_graph.add_edge(feature, typ, kind='FeatureTyping')

            elif ele['@type'] == 'FeatureMembership':
                owner = ele['owningType']['@id']
                feature = ele['memberFeature']['@id']

                # limit to part usages for now

                if self.session.get_metaclass_by_id(feature) == 'PartUsage':
                    self.part_featuring_graph.add_node(owner, name=self.session.get_name_by_id(ele_id=owner))
                    self.part_featuring_graph.add_node(feature, name=self.session.get_name_by_id(ele_id=feature))
                    self.part_featuring_graph.add_edge(owner, specific)

                    self.banded_featuring_graph.add_node(feature, name=self.session.get_name_by_id(ele_id=feature))
                    self.banded_featuring_graph.add_node(owner, name=self.session.get_name_by_id(ele_id=owner))
                    self.banded_featuring_graph.add_edge(owner, feature, kind='FeatureMembership')