import networkx as nx
from ..interpretation.m0_operators import *
from ..interpretation.interpretation import Instance, ValueHolder, LiveExpressionNode

class CalculationLabeledPropertyGraph():
    """
    A graph to represent the active expression tree in a model.
    """

    def __init__(self, dcg: nx.MultiDiGraph, instance_dict:dict):
        self.graph = dcg
        self.instance_dict=instance_dict

        self.solved_nodes = []

        self.components = list(nx.connected_components(dcg.to_undirected()))
        # flag to mark entire components as complete and able to be disregarded
        self.components_complete = [False for comp in self.components]

        self.unsolved_nodes = list(dcg.nodes)

    def solve_graph(self, lpg):
        # evaluating the expression tree is a reverse-order breadth-first search (cover all children of a given
        # node and then move up to that node)

        for m, comp in enumerate(self.components):
            connected_sub = nx.subgraph(self.graph, list(comp))
            if len(comp) == 2:
                # go through simple cases quickly
                leaf_side = [node for node in connected_sub.nodes if connected_sub.in_degree(node) == 0][0]
                m0_expr = self.instance_dict[leaf_side[0]][leaf_side[1]][leaf_side[2]-1]
                if 'Literal' in m0_expr.base_att['@type']:
                    evaluate_and_apply_literal(m0_expr, self.instance_dict)

                    comp_nodes = list(comp)

                    # Mark off nodes and components as solved
                    self.solved_nodes.append(comp_nodes[0])
                    self.solved_nodes.append(comp_nodes[1])

                    self.unsolved_nodes.remove(comp_nodes[0])
                    self.unsolved_nodes.remove(comp_nodes[1])

                    self.components_complete[m] = True
            else:
                #print(len(comp))
                sorted_sub = list(nx.topological_sort(connected_sub))
                #print("Sorted sub:")
                #for step in sorted_sub:
                    #print(self.instance_dict[step[0]][step[1]][step[2]-1])
                for index, step in enumerate(sorted_sub):
                    #print(step)
                    m0_obj = self.instance_dict[step[0]][step[1]][step[2]-1]
                    prev_steps = list(connected_sub.predecessors(step))
                    prev_steps_list = []
                    for prev_step in prev_steps:
                        prev_steps_list.append(self.instance_dict[prev_step[0]][prev_step[1]][prev_step[2]-1])

                    #print("Current Object")
                    #print(m0_obj)
                    #print("Predecessors")
                    #print(prev_steps_list)

                    if index == 0:
                        # need to have a literal or fre node here
                        if isinstance(m0_obj, LiveExpressionNode):
                            if 'Literal' in m0_obj.base_att['@type']:
                                evaluate_and_apply_literal(
                                    m0_obj,
                                    self.instance_dict
                                )
                                self.solved_nodes.append(step)
                                self.unsolved_nodes.remove(step)
                            elif m0_obj.base_att['@type'] == 'FeatureReferenceExpression':
                                evaluate_and_apply_fre(
                                    m0_obj,
                                    self.instance_dict
                                )
                                self.solved_nodes.append(step)
                                self.unsolved_nodes.remove(step)
                            else:
                                raise ValueError("Expression graph does not start with simple evaluation!")
                    else:
                        if isinstance(m0_obj, ValueHolder):
                            #print("ValueHolder at index = " + str(index))
                            self.solved_nodes.append(step)
                            self.unsolved_nodes.remove(step)
                            for prev_step in prev_steps:
                                m0_prev_obj = self.instance_dict[prev_step[0]][prev_step[1]][prev_step[2] - 1]
                                if isinstance(m0_prev_obj, ValueHolder):
                                    #print("Pressing value ahead from previous")
                                    m0_obj.value = m0_prev_obj.value
                        elif isinstance(m0_obj, LiveExpressionNode):
                            #print("LiveExpressionNode at index = " + str(index))
                            expr_type = m0_obj.base_att['@type']
                            if 'Literal' in expr_type:
                                evaluate_and_apply_literal(
                                    m0_obj,
                                    self.instance_dict
                                )
                                self.solved_nodes.append(step)
                                self.unsolved_nodes.remove(step)
                            elif expr_type == 'FeatureReferenceExpression':
                                evaluate_and_apply_fre(
                                    m0_obj,
                                    self.instance_dict
                                )
                                self.solved_nodes.append(step)
                                self.unsolved_nodes.remove(step)
                            elif expr_type == 'OperatorExpression':
                                if m0_obj.base_att['operator'] == 'collect':
                                    #print("Have come to collect. Previous steps length is " + str(len(prev_steps)))
                                    for prev_step in prev_steps:
                                        m0_prev_obj = self.instance_dict[prev_step[0]][prev_step[1]][prev_step[2] - 1]
                                        if m0_prev_obj.base_att['name'] == '$collection':
                                            print("Collection = " + str(m0_prev_obj))
                                            m0_collection = m0_prev_obj
                                        else:
                                            print("Path includes " + str(m0_prev_obj))
                                            m0_path = m0_prev_obj
                                    if len(prev_steps) == 1:
                                        prev_step = prev_steps[0]
                                        m0_prev_obj = self.instance_dict[prev_step[0]][prev_step[1]][prev_step[2] - 1]

                                    evaluate_and_apply_collect(
                                        m0_obj,
                                        self.instance_dict,
                                        m0_collection,
                                        m0_path,
                                        prev_step[1]
                                    )

                    print(self.instance_dict[step[0]][step[1]][step[2] - 1])


