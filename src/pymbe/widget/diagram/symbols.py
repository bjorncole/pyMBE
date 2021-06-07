from ipyelk.elements import Node, NodeProperties
from ipyelk.elements.shapes import Circle, Path, Point
from ipyelk.elements.symbol import EndpointSymbol


def make_arrow_symbol(identifier: str, r=6, closed=False) -> EndpointSymbol:
    return EndpointSymbol(
        element=Node(
            children=[
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list(
                            [(r / 2, -r / 3), (0, 0), (r / 2, r / 3)],
                            closed=closed,
                        ),
                    ),
                ),
            ],
        ),
        identifier=identifier,
        path_offset=Point(x=(-r / 1.75) if closed else 0, y=0),
        symbol_offset=Point(x=-1, y=0),
    )


def make_containment_symbol(identifier: str, r=6) -> EndpointSymbol:
    return EndpointSymbol(
        identifier=identifier,
        element=Node(
            children=[
                Node(
                    properties=NodeProperties(
                        shape=Circle(
                            radius=r,
                            x=r,
                            y=0,
                        )
                    )
                ),
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list([(0, 0), (2 * r, 0)]),
                    )
                ),
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list([(r, -r), (r, r)]),
                    )
                ),
            ]
        ),
        symbol_offset=Point(x=-1, y=0),
        path_offset=Point(x=-2 * r, y=0),
    )


def make_feature_typing_symbol(identifier: str, r=6) -> EndpointSymbol:
    return EndpointSymbol(
        element=Node(
            children=[
                Node(
                    properties=NodeProperties(
                        shape=Circle(
                            radius=r / 20,
                            x=r * 4 / 5,
                            y=r / 4,
                        ),
                    ),
                ),
                Node(
                    properties=NodeProperties(
                        shape=Circle(
                            radius=r / 20,
                            x=r * 4 / 5,
                            y=-r / 4,
                        ),
                    ),
                ),
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list(
                            [(r / 2, -r / 3), (0, 0), (r / 2, r / 3)],
                            closed=True,
                        ),
                    ),
                ),
            ],
        ),
        identifier=identifier,
        path_offset=Point(x=-r / 1.75, y=0),
        symbol_offset=Point(x=-1, y=0),
    )


def make_redefinition_symbol(identifier: str, r=6) -> EndpointSymbol:
    return EndpointSymbol(
        element=Node(
            children=[
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list(
                            [(r * 4 / 5, -r / 3), (r * 4 / 5, r / 3)],
                        ),
                    ),
                ),
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list(
                            [(r * 4 / 5, -r / 3), (r * 4 / 5, r / 3)],
                            closed=True,
                        ),
                    ),
                ),
            ],
        ),
        identifier=identifier,
        path_offset=Point(x=-r / 1.75, y=0),
        symbol_offset=Point(x=-1, y=0),
    )


def make_rhombus_symbol(identifier: str, r: float = 6) -> EndpointSymbol:
    return EndpointSymbol(
        identifier=identifier,
        element=Node(
            properties=NodeProperties(
                shape=Path.from_list(
                    [
                        (0, 0),
                        (r, r / 2),
                        (2 * r, 0),
                        (r, -r / 2),
                    ],
                    closed=True,
                )
            ),
        ),
        symbol_offset=Point(x=-1, y=0),
        path_offset=Point(x=-2 * r, y=0),
    )


def make_subsetting_symbol(identifier: str, r=6) -> EndpointSymbol:
    return EndpointSymbol(
        element=Node(
            children=[
                Node(
                    properties=NodeProperties(
                        shape=Circle(
                            radius=r / 5,
                            x=r / 5,
                            y=0,
                        ),
                    ),
                ),
                Node(
                    properties=NodeProperties(
                        shape=Path.from_list(
                            [(r, -r / 2.5), (r / 2.5, 0), (r, r / 2.5)],
                            closed=False,
                        ),
                    ),
                ),
            ],
        ),
        identifier=identifier,
        path_offset=Point(x=-r / 1.9, y=0),
        symbol_offset=Point(x=-1, y=0),
    )
