import networkx as nx

from pymbe.query.query import (
    get_features_typed_by_type,
    get_label_for_id,
    get_types_for_feature,
    roll_up_lower_multiplicity,
    roll_up_multiplicity_for_type,
    roll_up_upper_multiplicity,
)


from tests.conftest import kerbal_model_loaded_client


def test_feature_to_type1(kerbal_client, kerbal_lpg):

    engines_feat = '32c847a1-2184-4486-ba48-dbf6125ca638'
    engine_type_feat = '79cf7d24-37f7-404c-94b4-395cd1d0ee51'

    assert get_types_for_feature(kerbal_lpg, engines_feat) == [engine_type_feat]


def test_type_to_feature1(kerbal_client, kerbal_lpg):

    engines_feat = '32c847a1-2184-4486-ba48-dbf6125ca638'
    engine_type_feat = '79cf7d24-37f7-404c-94b4-395cd1d0ee51'

    assert get_features_typed_by_type(kerbal_lpg, engine_type_feat) == [engines_feat]


def test_type_to_feature2(simple_parts_client, simple_parts_lpg):

    port_type_id = 'f29c8a2e-a7d3-4685-bfbb-3d54b5dd704c'
    power_in_id = '7328c370-26d7-40e4-9a36-c88ef76c7d30'
    power_out_id = 'babeb025-52f3-4ebe-9f0f-0414a4b6240d'

    print(get_features_typed_by_type(simple_parts_lpg, port_type_id))

    assert power_in_id in get_features_typed_by_type(simple_parts_lpg, port_type_id) and \
            power_out_id in get_features_typed_by_type(simple_parts_lpg, port_type_id)


def test_banded_graph_paths1(kerbal_lpg):

    rocket_id = '62fc7eb7-0637-4201-add7-4d2758980d2f'
    engines_feat = '32c847a1-2184-4486-ba48-dbf6125ca638'

    all_paths = nx.all_simple_paths(
        kerbal_lpg.get_projection("Expanded Banded Graph"),
        engines_feat,
        rocket_id
    )

    path_lists = list(all_paths)

    for path in path_lists:
        path_naming = []
        for item in path:
            path_naming.append(get_label_for_id(item, kerbal_lpg.nodes))

        print(path_naming)

    assert len(path_lists) == 1


def test_banded_graph_paths2(kerbal_lpg):

    rocket_id = '62fc7eb7-0637-4201-add7-4d2758980d2f'
    ft200_feat_id = 'cc585eec-c66c-48aa-b319-1395a0c8e292'

    all_paths = nx.all_simple_paths(
        kerbal_lpg.get_projection("Expanded Banded Graph"),
        ft200_feat_id,
        rocket_id
    )

    path_lists = list(all_paths)

    for path in path_lists:
        path_naming = []
        for item in path:
            path_naming.append(get_label_for_id(item, kerbal_lpg.nodes))

        print(path_naming)

    assert len(path_lists) == 1


def test_banded_graph_paths3(simple_parts_lpg):

    power_group_id = 'eb96afae-0f09-4912-861e-705bb33a4202'
    power_in_port_id = '7328c370-26d7-40e4-9a36-c88ef76c7d30'

    ebg = simple_parts_lpg.get_projection("Expanded Banded Graph")

    assert power_group_id in list(simple_parts_lpg.nodes)
    assert power_in_port_id in list(simple_parts_lpg.nodes)

    assert power_group_id in list(ebg.nodes)
    assert power_in_port_id in list(ebg.nodes)

    all_paths = nx.all_simple_paths(
        simple_parts_lpg.get_projection("Expanded Banded Graph"),
        power_in_port_id,
        power_group_id
    )

    path_lists = list(all_paths)

    for path in path_lists:
        path_naming = []
        for item in path:
            path_naming.append(get_label_for_id(item, simple_parts_lpg.nodes))

        print(path_naming)

    assert len(path_lists) == 1


def test_feature_multiplicity_rollup1(kerbal_lpg):
    engines_feat = '32c847a1-2184-4486-ba48-dbf6125ca638'
    stages_feat = '442722b5-8d08-46e4-ad5f-e6e2dd28d6f6'

    assert engines_feat in list(kerbal_lpg.nodes.keys())
    assert stages_feat in list(kerbal_lpg.nodes.keys())

    engines_lower_mult = roll_up_lower_multiplicity(
        lpg=kerbal_lpg,
        feature=kerbal_lpg.nodes[engines_feat],
    )

    engines_upper_mult = roll_up_upper_multiplicity(
        lpg=kerbal_lpg,
        feature=kerbal_lpg.nodes[engines_feat],
    )

    stages_lower_mult = roll_up_lower_multiplicity(
        lpg=kerbal_lpg,
        feature=kerbal_lpg.nodes[stages_feat],
    )

    stages_upper_mult = roll_up_upper_multiplicity(
        lpg=kerbal_lpg,
        feature=kerbal_lpg.nodes[stages_feat],
    )

    assert engines_lower_mult == 0
    assert engines_upper_mult == 40

    assert stages_lower_mult == 1
    assert stages_upper_mult == 5


def test_type_multiplicity_rollup1(kerbal_lpg):

    real_type = 'ede2b2e7-9280-4932-9453-134bf460892f'
    liquid_engine_type = '79cf7d24-37f7-404c-94b4-395cd1d0ee51'
    rocket_type = '62fc7eb7-0637-4201-add7-4d2758980d2f'

    real_ele = kerbal_lpg.nodes[real_type]
    liquid_engine_ele = kerbal_lpg.nodes[liquid_engine_type]
    rocket_ele = kerbal_lpg.nodes[rocket_type]

    liquid_upper = roll_up_multiplicity_for_type(
        kerbal_lpg,
        liquid_engine_ele,
        "upper"
    )

    rocket_upper = roll_up_multiplicity_for_type(
        kerbal_lpg,
        rocket_ele,
        "upper"
    )

    assert liquid_upper == 40
    assert rocket_upper == 0


def test_type_multiplicity_rollup2(simple_parts_lpg):

    port_type_id = 'f29c8a2e-a7d3-4685-bfbb-3d54b5dd704c'
    power_in_id = '7328c370-26d7-40e4-9a36-c88ef76c7d30'
    power_out_id = 'babeb025-52f3-4ebe-9f0f-0414a4b6240d'

    port_type = simple_parts_lpg.nodes[port_type_id]

    port_upper = roll_up_multiplicity_for_type(
        simple_parts_lpg,
        port_type,
        "upper"
    )

    power_in_mult = roll_up_upper_multiplicity(
        lpg=simple_parts_lpg,
        feature=simple_parts_lpg.nodes[power_in_id],
    )

    power_out_mult = roll_up_upper_multiplicity(
        lpg=simple_parts_lpg,
        feature=simple_parts_lpg.nodes[power_out_id],
    )

    assert power_in_mult == 1
    assert power_out_mult == 1

    # currently failing because we are counting connector ends as separate instances

    assert port_upper == 2
