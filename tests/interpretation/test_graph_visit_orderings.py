from pymbe.interpretation.interp_playbooks import (
    build_expression_sequence_templates,
    build_sequence_templates,
)
from pymbe.interpretation.results import *


ROCKET_BUILDING = "Model::Kerbal::Rocket Building::"
PARTS_LIBRARY = "Model::Kerbal::Parts Library::"

SIMPLE_MODEL = "Model::Simple Parts Model::"
PARTS_LIBRARY = "Model::Simple Parts Model::Fake Library::"


def test_feature_sequence_templates1(kerbal_client, kerbal_lpg, kerbal_stable_names):
    *_, qualified_name_to_id = kerbal_stable_names

    seq_templates = build_sequence_templates(kerbal_lpg)

    assert len(seq_templates) == 39

    solid_booster_id = qualified_name_to_id[f"{ROCKET_BUILDING}Solid Booster <<PartDefinition>>"]
    boosters_id = qualified_name_to_id[f"{ROCKET_BUILDING}Solid Stage::boosters: Solid Booster <<PartUsage>>"]
    liquid_stage_id = qualified_name_to_id[f"{ROCKET_BUILDING}Liquid Stage <<PartDefinition>>"]
    engines_id = qualified_name_to_id[f"{ROCKET_BUILDING}Liquid Stage::engines: Liquid Engine <<PartUsage>>"]
    tanks_id = qualified_name_to_id[f"{ROCKET_BUILDING}Liquid Stage::tanks: Fuel Tank Section <<PartUsage>>"]
    krp_mass_id = qualified_name_to_id[f"{ROCKET_BUILDING}Kerbal Rocket Part::Mass: Real <<AttributeUsage>>"]

    print(pprint_double_id_list(seq_templates, kerbal_lpg.model))

    assert [
        liquid_stage_id,
        engines_id] in seq_templates

    assert(any([krp_mass_id in seq for seq in seq_templates]))

    assert (any([
        (engines_id in seq) and
        (liquid_stage_id in seq)
        for seq in seq_templates])
    )

    assert (any([
        (tanks_id in seq) and
        (liquid_stage_id in seq)
        for seq in seq_templates])
    )


def test_feature_sequence_templates2(kerbal_lpg, kerbal_stable_names):
    *_, qualified_name_to_id = kerbal_stable_names

    seq_templates = build_sequence_templates(kerbal_lpg)

    coupler_usage_id = qualified_name_to_id[
        f"{ROCKET_BUILDING}Rocket::stages: Rocket Stage::Coupler to "
        f"Carrying Stage: Coupler <<PartUsage>>"]
    rocket_id = qualified_name_to_id[f"{ROCKET_BUILDING}Rocket <<PartDefinition>>"]
    stages_feat = qualified_name_to_id[f"{ROCKET_BUILDING}Rocket::stages: Rocket Stage <<PartUsage>>"]
    sep_force_id = qualified_name_to_id[
        f"{ROCKET_BUILDING}Rocket::stages: Rocket Stage::Coupler to Carrying Stage: "
        f"Coupler::Separation Force: Real <<AttributeUsage>>"]

    print(pprint_double_id_list(seq_templates, kerbal_lpg.model))

    assert [
        rocket_id,
        stages_feat,
        coupler_usage_id,
        sep_force_id] in seq_templates


def test_feature_sequence_templates3(kerbal_lpg, kerbal_stable_names):
    *_, qualified_name_to_id = kerbal_stable_names

    seq_templates = build_sequence_templates(kerbal_lpg)

    coupler_usage_id = qualified_name_to_id[
        f"{ROCKET_BUILDING}Rocket::stages: Rocket Stage::Coupler to "
        f"Carrying Stage: Coupler <<PartUsage>>"]
    rocket_id = qualified_name_to_id[f"{ROCKET_BUILDING}Rocket <<PartDefinition>>"]
    sep_force_id = qualified_name_to_id[
        f"{ROCKET_BUILDING}Rocket::stages: Rocket Stage::Coupler to Carrying Stage: "
        f"Coupler::Separation Force: Real <<AttributeUsage>>"]

    print(pprint_double_id_list(seq_templates, kerbal_lpg.model))

    assert [
        rocket_id,
        coupler_usage_id,
        sep_force_id] not in seq_templates


def test_feature_sequence_templates4(simple_parts_lpg, simple_parts_stable_names):
    *_, qualified_name_to_id = simple_parts_stable_names

    seq_templates = build_sequence_templates(simple_parts_lpg)

    power_group_id = qualified_name_to_id[f"{SIMPLE_MODEL}Power Group: Part <<PartUsage>>"]
    power_user_part_id = qualified_name_to_id[f"{SIMPLE_MODEL}Power Group: Part::Power User: Part <<PartUsage>>"]
    power_in_port_id = qualified_name_to_id[f"{SIMPLE_MODEL}Power Group: Part::Power User: "
                                            f"Part::Power In: Port <<PortUsage>>"]

    print(seq_templates)

    assert [
        power_group_id,
        power_user_part_id,
        power_in_port_id] in seq_templates


def test_expression_sequence_templates(kerbal_lpg):
    fts_full_mass = "004a1b5f-4bfc-4460-9f38-1e7b4caba6e5"
    ft200_full_mass = "1e5a0ed7-8b41-4ab4-a433-8f7eedd75833"
    ft100_full_mass = "a57b423b-5c0c-4057-be6b-689abcb536b2"
    liquid_stage_full_mass = "7beafac8-c1c1-4b1b-ae21-d3c9a733531c"
    top_plus = "b51bb349-e210-4be8-be64-e749ea4e563b"
    tank_mass_sum_1 = "700d97d1-410a-459c-ad09-8792c27e2803"
    collect_1 = "d6644a0a-6eef-49c1-a770-60886073554c"
    collect_1_result = "31f8c4bd-9700-4bc3-9970-3eb5451f0203"
    full_mass_dot = "ad0bff53-eebe-4446-a8df-4db0b7187707"
    fre_1 = "2665fb1b-1f12-4f13-a977-0f060915773e"
    fre_1_result = "6cfb516b-6045-454e-a521-83b747acef7e"

    expr_sequences = build_expression_sequence_templates(lpg=kerbal_lpg)
    top_plus_paths = 0
    direct_literals = 0

    fre_result_found = False

    # big roll-up
    for seq in expr_sequences:
        if top_plus in seq:
            top_plus_paths += 1
        if fre_1_result in seq:
            fre_result_found = True

    # individual literal expression value assignments
    for seq in expr_sequences:
        if "Literal" in kerbal_lpg.nodes[seq[0]]["@type"]:
            direct_literals += 1
            assert len(seq) == 2
        # each sequence should end with the result
        assert kerbal_lpg.nodes[seq[len(seq) - 1]]["@type"] == "Feature"

    assert top_plus_paths == 17
    assert direct_literals == 26
    assert len(expr_sequences) == 43

    assert fre_result_found
