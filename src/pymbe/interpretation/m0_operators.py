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