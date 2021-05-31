import networkx as nx

from ..interpretation.m0_operators import *
from ..interpretation.interpretation import Instance, ValueHolder, LiveExpressionNode
from ..interpretation.results import *


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
                        print(get_label_for_id(step[1], lpg.nodes) + ", id = " + step[1] + " has no elements")
                    else:

                        for index, source in enumerate(source_instances):
                            target_instances[index][-1].value = source[-1].value
            elif step[2] == 'Redefinition':
                if step[0] in self.instance_dict:
                    source_instances = self.instance_dict[step[0]]
                    target_instances = self.instance_dict[step[1]]

                    for indx, sorc in enumerate(source_instances):
                        for jndx, targ in enumerate(target_instances):
                            sorce_base = sorc[0:-1]
                            targ_base = targ[0:-1]
                            if sorce_base == targ_base:
                                targ[-1].value = sorc[-1].value

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
                elif lpg.nodes[step[0]]['@type'] == 'FeatureReferenceExpression':
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

                elif lpg.nodes[step[0]]['@type'] == 'OperatorExpression':
                    if lpg.nodes[step[0]]['operator'] == 'collect':
                        source_instances = self.instance_dict[step[0]]
                        target_instances = self.instance_dict[step[1]]

                        collect_sub_expressions = []
                        collect_sub_expression_results = []
                        collect_sub_inputs = []
                        for member in lpg.nodes[step[0]]['member']:
                            if lpg.nodes[member['@id']]['@type'] in ('Expression', 'FeatureReferenceExpression'):
                                collect_sub_expressions.append(lpg.nodes[member['@id']])
                                collect_sub_expression_results.append(lpg.nodes[lpg.nodes[member['@id']]['result']['@id']])

                        for member in lpg.nodes[step[0]]['input']:
                            collect_sub_inputs.append(lpg.nodes[member['@id']])

                        for index, m0_operator_seq in enumerate(source_instances):
                            input_point = None
                            input_instances = self.instance_dict[collect_sub_inputs[0]['@id']]
                            for input_inst in input_instances:
                                if input_inst[0] == m0_operator_seq[0]:
                                    input_point = input_inst[-1]
                            path_point = None
                            input_instances = self.instance_dict[collect_sub_expression_results[1]['@id']]
                            for input_inst in input_instances:
                                if input_inst[0] == m0_operator_seq[0]:
                                    path_point = input_inst[-1]

                            #print("Calling collect with base = " + str(m0_operator_seq[0]) + ", collection input " +
                            #      str(input_point) + ", and path input " + str(path_point))

                            if path_point.value is None:
                                print("Path point value is empty! " + str(path_point))
                            else:
                                evaluate_and_apply_collect(
                                    m0_operator_seq[0],
                                    m0_operator_seq[-1],
                                    self.instance_dict,
                                    input_point,
                                    path_point,
                                    target_instances[index][-1]
                                )

                        self.solved_nodes.append(step[0])
                        self.solved_nodes.append(step[1])

                        self.unsolved_nodes.remove(step[0])
                        self.unsolved_nodes.remove(step[1])

                    elif lpg.nodes[step[0]]['operator'] == '+':
                        source_instances = self.instance_dict[step[0]]
                        target_instances = self.instance_dict[step[1]]

                        for member in lpg.nodes[step[0]]['input']:
                            collect_sub_inputs.append(lpg.nodes[member['@id']])

                        plus_inputs = []

                        for member in lpg.nodes[step[0]]['input']:
                            plus_inputs.append(lpg.nodes[member['@id']])

                        for index, m0_operator_seq in enumerate(source_instances):
                            x_point = None
                            y_point = None
                            for input_index, input in enumerate(plus_inputs):
                                input_instances = self.instance_dict[input['@id']]
                                for input_inst in input_instances:
                                    if input_inst[0] == m0_operator_seq[0]:
                                        if input_index == 0:
                                            x_point = input_inst[-1]
                                        elif input_index == 1:
                                            y_point = input_inst[-1]

                            evaluate_and_apply_plus(
                                x_point,
                                y_point,
                                target_instances[index][-1]
                            )

                elif lpg.nodes[step[0]]['@type'] == "InvocationExpression":
                    invoke_type = lpg.nodes[lpg.nodes[step[0]]['type'][0]['@id']]

                    source_instances = self.instance_dict[step[0]]
                    target_instances = self.instance_dict[step[1]]

                    if invoke_type['name'] == 'sum':
                        sum_inputs = []

                        for member in lpg.nodes[step[0]]['input']:
                            sum_inputs.append(lpg.nodes[member['@id']])

                        for index, m0_operator_seq in enumerate(source_instances):
                            input_point = None
                            input_instances = self.instance_dict[sum_inputs[0]['@id']]
                            for input_inst in input_instances:
                                if input_inst[0] == m0_operator_seq[0]:
                                    input_point = input_inst[-1]

                            evaluate_and_apply_sum(
                                input_point,
                                target_instances[index][-1]
                            )

    def solve_graph_with_openmdao(self, lpg):
        """
        Similar to solve graph, but use OpenMDAO to fill in values rather than literal expressions
        :param lpg:
        :return:
        """
        pass

        # Look through the calculation list and the relevant sequences, use this to build needed alternative
        # OpenMDAO problems - turn over passing of variables to OpenMDAO - ignore the Assignment / Value Binding steps

        # Once problems are built, execute and bring results back to input / result parameter sequences as needed
