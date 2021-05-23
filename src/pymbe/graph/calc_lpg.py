import networkx as nx
from ..interpretation.m0_operators import *
from ..interpretation.interpretation import Instance, ValueHolder, LiveExpressionNode


class CalculationGroup:
    """
    A graph to represent the active expression tree in a model.
    """

    def __init__(self, eig: nx.MultiDiGraph, instance_dict:dict, calculation_list: list):
        self.graph = eig
        self.instance_dict=instance_dict

        self.solved_nodes = []
        self.unsolved_nodes = list(eig.nodes)

        self.calculation_list = calculation_list

    def solve_graph(self, lpg):
        # evaluating the expression tree is a reverse-order breadth-first search (cover all children of a given
        # node and then move up to that node)

        for step in self.calculation_list:
            if step[2] in ('Assignment', 'ValueBinding'):
                if step[0] in self.instance_dict:
                    source_instances = self.instance_dict[step[0]]
                    target_instances = self.instance_dict[step[1]]

                    if len(target_instances) == 0:
                        print(source_instances)
                        print(get_label_for_id(step[1], lpg.nodes) + " has no elements")
                    else:

                        for index, source in enumerate(source_instances):
                            target_instances[index][-1].value = source[-1].value
            elif step[2] == 'Output':
                if 'Literal' in lpg.nodes[step[0]]['@type']:
                    source_instances = self.instance_dict[step[0]]
                    target_instances = self.instance_dict[step[1]]

                    for index, seq in enumerate(source_instances):
                        evaluate_and_apply_literal(seq[-1], target_instances[index][-1])

                    self.solved_nodes.append(step[0])
                    self.solved_nodes.append(step[1])

                    self.unsolved_nodes.remove(step[0])
                    self.unsolved_nodes.remove(step[1])
                elif lpg.nodes[step[0]] == 'FeatureReferenceExpression':
                    source_instances = self.instance_dict[step[0]]
                    target_instances = self.instance_dict[step[1]]

                    for m0_obj in source_instances:
                        evaluate_and_apply_fre(
                            m0_obj[-1],
                            self.instance_dict
                        )

                    self.solved_nodes.append(step[0])
                    self.solved_nodes.append(step[1])

                    self.unsolved_nodes.remove(step[0])
                    self.unsolved_nodes.remove(step[1])

                elif lpg.nodes[step[0]] == 'OperatorExpression':
                    if m0_obj.base_att['operator'] == 'collect':
                        source_instances = self.instance_dict[step[0]]
                        target_instances = self.instance_dict[step[1]]

                        print(source_instances)
                        print(target_instances)

                        evaluate_and_apply_collect(
                            self.instance_dict[step[0]][step[1]][0],
                            m0_obj,
                            self.instance_dict,
                            m0_collection,
                            m0_path,
                            prev_step[1]
                        )

                        self.solved_nodes.append(step[0])
                        self.solved_nodes.append(step[1])

                        self.unsolved_nodes.remove(step[0])
                        self.unsolved_nodes.remove(step[1])


