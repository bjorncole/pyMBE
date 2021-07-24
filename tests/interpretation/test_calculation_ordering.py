from pymbe.interpretation.calc_dependencies import generate_execution_order

import logging
from pymbe.interpretation.results import *

ROCKET_BUILDING = "Model::Kerbal::Rocket Building::"
PARTS_LIBRARY = "Model::Kerbal::Parts Library::"


def test_kerbal_calc_order1(kerbal_lpg, kerbal_random_stage_5_complete, kerbal_stable_names):
    # check that the right number of values are created for their features

    *_, qualified_name_to_id = kerbal_stable_names

    liquid_stage_type = qualified_name_to_id[f'{ROCKET_BUILDING}Liquid Stage <<PartDefinition>>']

    number_liquid_stages = len(kerbal_random_stage_5_complete[liquid_stage_type])

    dcg = generate_execution_order(kerbal_lpg)

    # the execution order will be ordered for examination

    sum_1_result = qualified_name_to_id[f'{ROCKET_BUILDING}Liquid Stage::Full Mass: Real::+ (sum (collect (FRE.engines)),'
                                     f' sum (collect (FRE.tanks))) => $result::sum (collect (FRE.tanks)) => $result::'
                                     f'sum (collect (FRE.tanks)) <<Feature>>']  # Result of the sum Expression on Full Mass
    top_plus = qualified_name_to_id[f'{ROCKET_BUILDING}Liquid Stage::Full Mass: Real::+ (sum (collect (FRE.engines)), ' +
                                 'sum (collect (FRE.tanks))) => $result <<OperatorExpression>>']

    sum_1_in_dcg = None
    plus_in_dcg = None

    for item in dcg:
        if item[0] == sum_1_result:
            sum_1_in_dcg = sum_1_result
        if item[0] == top_plus:
            plus_in_dcg = top_plus

    assert sum_1_in_dcg is not None
    assert plus_in_dcg is not None
    assert len(kerbal_random_stage_5_complete[sum_1_result]) == len(kerbal_random_stage_5_complete[liquid_stage_type])
    assert len(kerbal_random_stage_5_complete[top_plus]) == len(kerbal_random_stage_5_complete[liquid_stage_type])