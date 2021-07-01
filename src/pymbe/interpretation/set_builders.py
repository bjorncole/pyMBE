import itertools
import random

from .interpretation import Instance, ValueHolder, LiveExpressionNode
from ..label import get_label

# Adaptations to simplify dictionary production

# Random production of dictionaries through a couple of techniques:

# 1. Generate instances up to a specific quantity (a la classifier dictionaries)

# 2. Sub-select from other sets (a la feature dictionaries)

# In both cases, use a reference sequence to find the minimal length intepretations
#### Both classifiers and features can be made this way, just difference of lengths


def create_set_with_new_instances(
    sequence_template: list,
    quantities: list,
    name_hints: dict,
) -> list:
    """
    Generate a list of lists with pre-set quantities and templates based on M1 model Types.

    New Instances will be constructed at each position in the sequence.
    :param sequence_template: Sequence of Types (full data) to use as data sources for new Instances
    :param quantities: Number of Instances to create for each sequence
    :param name_hints: Pre-made short names to support instance naming
    :return: A set of instances built into a Cartesian product based on a type sequence
    """

    individual_lists = []

    for index, m1_type in enumerate(sequence_template):
        new_list = []
        for m in range(0, quantities[index]):
            if m1_type['@type'] not in ('AttributeDefinition', 'AttributeUsage', 'DataType'):
                new_list.append(
                    Instance(
                        m1_type['name'],
                        m,
                        name_hints
                    )
                )
            else:
                new_list.append(
                    ValueHolder(
                        [],
                        m1_type['name'],
                        None,
                        m1_type,
                        m
                    )
                )
        individual_lists.append(new_list)

    # walk the sequence and generate an appropriately named instance
    if len(sequence_template) > 1:
        cartesian_of_lists = [
            list(cartesian)
            for cartesian in itertools.product(*individual_lists)
        ]
    else:
        cartesian_of_lists = [
            [individual]
            for individual in individual_lists[0]
        ]
    return cartesian_of_lists


def extend_sequences_by_sampling(
    previous_sequences: list,
    lower_mult: int,
    upper_mult: int,
    sample_set: list,
    fallback_to_generate: bool,
    fallback_type: dict,
    all_elements: dict
) -> list:
    """
    Extends a set of sequences by random numbers of instances drawn from a sample set

    :param previous_sequences: The set of sequences of a length n - 1 of desired
    :param lower_mult: lower bound on how many to draw from the sample set
    :param upper_mult: upper bound on how many to draw from the sample set
    :param sample_set: the set of Instances from which to draw to extend input sequences
    :param fallback_to_generate: Whether or not to make new instances if a sample set is not present
    :param fallback_type: The type to use as the fallback
    :param all_elements: Reference to all elements (for label generation)
    :return:
    """

    # FIXME: Need to be sure that each instance is drawn once even when multiple features have the same type!

    total_draw, draws_per = 0, []
    for _ in range(0, len(previous_sequences)):
        draw = random.randint(lower_mult, upper_mult)
        total_draw = total_draw + draw
        draws_per.append(draw)

    set_extended = []
    if len(sample_set) == 0 and fallback_to_generate:
        new_list = []
        last_draw = 0
        for m in range(0, total_draw):
            new_instance = Instance(
                get_label(fallback_type, all_elements),
                m,
                [],
            )

            new_list.append(new_instance)

        for index, seq in enumerate(previous_sequences):
            for pull in new_list[last_draw:last_draw + draws_per[index]]:
                new_seq = []
                new_seq = new_seq + seq
                new_seq.append(pull)

                # TODO: Look at making a generator instead

                set_extended.append(new_seq)

            last_draw = last_draw + draws_per[index]
    else:
        try:
            pulled_instances = random.sample(sample_set, total_draw)

            last_draw = 0
            for index, seq in enumerate(previous_sequences):
                for pull in pulled_instances[last_draw:last_draw+draws_per[index]]:
                    new_seq = []
                    new_seq = new_seq + seq
                    new_seq.append(pull)

                    # TODO: Look at making a generator instead

                    set_extended.append(new_seq)

                last_draw = last_draw + draws_per[index]
        except ValueError:
            print("Sample Set is:")
            print(sample_set)
            print("Previous sequences include:")
            print(previous_sequences)
            print(draws_per)
            raise ValueError("Tried to pull " + str(total_draw) + " instances from a length of " + str(len(sample_set)))

    return set_extended


def extend_sequences_with_new_expr(
    previous_sequences: list,
    expr_string: str,
    expr: dict
) -> list:

    new_sequences = []

    for indx, seq in enumerate(previous_sequences):
        new_holder = LiveExpressionNode(
            seq,
            expr_string,
            expr
        )

        new_sequence = []
        new_sequence = new_sequence + seq
        new_sequence.append(new_holder)

        new_sequences.append(new_sequence)

    return new_sequences


def extend_sequences_with_new_value_holder(
    previous_sequences: list,
    base_name: str,
    base_ele: dict
) -> list:

    new_sequences = []

    for indx, seq in enumerate(previous_sequences):
        new_holder = ValueHolder(
            seq,
            base_name,
            None,
            base_ele,
            indx
        )

        new_sequence = []
        new_sequence = new_sequence + seq
        new_sequence.append(new_holder)

        new_sequences.append(new_sequence)

    return new_sequences