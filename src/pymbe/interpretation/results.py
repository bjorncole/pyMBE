# A set of tools to make interpretations easier to read
from ..label import get_label
from ..label import get_label_for_id

def pprint_interpretation(interpretation: dict, all_elements: dict) -> list:
    print_lines = []
    for key, val in interpretation.items():
        print_lines.append(get_label(all_elements[key], all_elements) + ', id = ' + key + ', size = ' + str(len(val)))
        short_list = []
        for indx, ind_val in enumerate(val):
            if indx < 5:
                short_list.append(ind_val)
        if len(val) > 4:
            short_list.append(['..'])

        print_lines.extend(short_list)
    return print_lines


def pprint_single_id_list(list_to_print: list, all_elements: dict) -> list:
    print_lines = []
    for item in list_to_print:
        print_lines.append(get_label_for_id(item, all_elements))

    return print_lines


def pprint_double_id_list(list_to_print: list, all_elements: dict) -> list:
    print_lines = []
    for seq in list_to_print:
        seq_line = []
        for item in seq:
            seq_line.append(get_label_for_id(item, all_elements))
        print_lines.append(seq_line)

    return print_lines