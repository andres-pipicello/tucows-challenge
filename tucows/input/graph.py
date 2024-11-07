from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional


@dataclass
class Graph:
    class Meta:
        name = "graph"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )

    @dataclass
    class Nodes:
        node: List["Graph.Nodes.Node"] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass
        class Node:
            id: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "required": True,
                },
            )
            name: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "required": True,
                },
            )

    @dataclass
    class Edges:
        edge: List["Graph.Edges.Edge"] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass
        class Edge:
            id: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "required": True,
                },
            )
            from_value: Optional[str] = field(
                default=None,
                metadata={
                    "name": "from",
                    "type": "Element",
                    "required": True,
                },
            )
            to: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "required": True,
                },
            )
            cost: Optional[Decimal] = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
