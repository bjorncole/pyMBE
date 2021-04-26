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

