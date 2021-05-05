from ..interpretation.interpretation import LiveExpressionNode
from ..graph.lpg import SysML2LabeledPropertyGraph

def sequence_dot_operator(left_item, right_side_seqs):
    left_len = len(left_item)
    right_len = len(right_side_seqs[0])
    # print('Left is ' + str(left_len) + ' right is ' + str(right_len))
    matched_items = []

    for right_item in right_side_seqs:
        # print(str(right_item[0:(right_len-1)]))
        if left_len != right_len:
            if str(left_item) == str(right_item[0:(right_len - 1)]):
                matched_items.append(right_item)
        else:
            if str(left_item[1:None]) == str(right_item[0:(right_len - 1)]):
                matched_items.append(right_item)

    return matched_items

def evaluate_collect(
    m0_expr: LiveExpressionNode,
    full_seq: list,
    lpg: SysML2LabeledPropertyGraph
) -> list:
    # FIXME: Implement collector over the embedded sequence

    # Look at the base attribute in the expression node to find which sequences to collect from and apply the
    # sequence dot operator and others as needed

    pass

def evaluate_fre(
    m0_expr: LiveExpressionNode,
    instance_dict: dict
) -> list:
    """
    Evaluate a feature reference expression at m0, e.g., return the list of sequences
    :param m0_expr:
    :param instance_dict:
    :return:
    """

    referent_id = m0_expr.base_att['referent']['@id']
    if referent_id in instance_dict:
        return instance_dict[referent_id]
    else:
        return []

def evaluate_and_apply_literal(
    m0_expr: LiveExpressionNode,
    instance_dict: dict
) -> list:
    """
    Evaluate a literal expression at m0, pushing the value to all instances of a viable result feature
    :param m0_expr:
    :param instance_dict:
    :return:
    """

    literal_value = m0_expr.base_att['value']
    literal_result = m0_expr.base_att['result']['@id']
    target_list = instance_dict[literal_result]
    for target in target_list:
        target[-1].value = literal_value