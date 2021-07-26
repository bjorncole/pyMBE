from ipyelk.elements import Node, NodeProperties
from ipyelk.elements.shapes import Circle, Path, Point
from ipyelk.elements.symbol import EndpointSymbol


def make_arrow_symbol(identifier: str, size=6, closed=False) -> EndpointSymbol:
    return EndpointSymbol(
        element=Node(
            children=[
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list(
                            [(size / 2, -size / 3), (0, 0), (size / 2, size / 3)],
                            closed=closed,
                        ),
                    ),
                ),
            ],
        ),
        identifier=identifier,
        path_offset=Point(x=(-size / 1.75) if closed else 0, y=0),
        symbol_offset=Point(x=-1, y=0),
    )


def make_containment_symbol(identifier: str, size=6) -> EndpointSymbol:
    return EndpointSymbol(
        identifier=identifier,
        element=Node(
            children=[
                Node(
                    properties=NodeProperties(
                        shape=Circle(
                            radius=size,
                            x=size,
                            y=0,
                        )
                    )
                ),
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list([(0, 0), (2 * size, 0)]),
                    )
                ),
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list([(size, -size), (size, size)]),
                    )
                ),
            ]
        ),
        symbol_offset=Point(x=-1, y=0),
        path_offset=Point(x=-2 * size, y=0),
    )


def make_feature_typing_symbol(identifier: str, size=6) -> EndpointSymbol:
    return EndpointSymbol(
        element=Node(
            children=[
                Node(
                    properties=NodeProperties(
                        shape=Circle(
                            radius=size / 20,
                            x=size * 4 / 5,
                            y=size / 4,
                        ),
                    ),
                ),
                Node(
                    properties=NodeProperties(
                        shape=Circle(
                            radius=size / 20,
                            x=size * 4 / 5,
                            y=-size / 4,
                        ),
                    ),
                ),
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list(
                            [(size / 2, -size / 3), (0, 0), (size / 2, size / 3)],
                            closed=True,
                        ),
                    ),
                ),
            ],
        ),
        identifier=identifier,
        path_offset=Point(x=-size / 1.75, y=0),
        symbol_offset=Point(x=-1, y=0),
    )


def make_redefinition_symbol(identifier: str, size=6) -> EndpointSymbol:
    return EndpointSymbol(
        element=Node(
            children=[
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list(
                            [(size * 4 / 5, -size / 3), (size * 4 / 5, size / 3)],
                        ),
                    ),
                ),
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list(
                            [(size / 2, -size / 3), (0, 0), (size / 2, size / 3)],
                            closed=True,
                        ),
                    ),
                ),
            ],
        ),
        identifier=identifier,
        path_offset=Point(x=-size / 1.75, y=0),
        symbol_offset=Point(x=-1, y=0),
    )


def make_rhombus_symbol(identifier: str, size: float = 6) -> EndpointSymbol:
    return EndpointSymbol(
        identifier=identifier,
        element=Node(
            properties=NodeProperties(
                shape=Path.from_list(
                    [
                        (0, 0),
                        (size, size / 2),
                        (2 * size, 0),
                        (size, -size / 2),
                    ],
                    closed=True,
                )
            ),
        ),
        symbol_offset=Point(x=-1, y=0),
        path_offset=Point(x=-2 * size, y=0),
    )


def make_subsetting_symbol(identifier: str, size=6) -> EndpointSymbol:
    return EndpointSymbol(
        element=Node(
            children=[
                Node(
                    properties=NodeProperties(
                        shape=Circle(
                            radius=size / 5,
                            x=size / 5,
                            y=0,
                        ),
                    ),
                ),
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list(
                            [(size, -size / 2.5), (size / 2.5, 0), (size, size / 2.5)],
                            closed=False,
                        ),
                    ),
                ),
            ],
        ),
        identifier=identifier,
        path_offset=Point(x=-size / 1.9, y=0),
        symbol_offset=Point(x=-1, y=0),
    )
