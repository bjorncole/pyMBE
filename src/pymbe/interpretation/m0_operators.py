from ..interpretation.interpretation import LiveExpressionNode, ValueHolder
from ..graph.lpg import SysML2LabeledPropertyGraph
from ..label import get_label_for_id

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

def evaluate_and_apply_collect(
    m0_expr: LiveExpressionNode,
    instance_dict: dict,
    m0_collection_input: ValueHolder,
    m0_collection_path: ValueHolder
) -> None:

    print("Applying collect to " + str(m0_collection_input))
    # apply the dot operator
    path_result = []
    for collect_seq in m0_collection_input.value:
        collect_match = sequence_dot_operator(collect_seq, m0_collection_path.value)
        path_result.append(collect_match)
    collect_result = m0_expr.base_att['result']['@id']
    print("Collect result is " + str(collect_result))

def evaluate_and_apply_fre(
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
        fre_result = m0_expr.base_att['result']['@id']
        target_list = instance_dict[fre_result]
        for target in target_list:
            target[-1].value = instance_dict[referent_id]
        return instance_dict[referent_id]
    else:
        return

def evaluate_and_apply_literal(
    m0_expr: LiveExpressionNode,
    instance_dict: dict
) -> None:
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