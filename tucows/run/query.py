import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin, config
from loguru import logger
from sqlalchemy import select, literal, VARCHAR, tuple_
from sqlalchemy.dialects.postgresql import ARRAY, array, Any
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import rank

from tucows.log import setup_loguru_logging_intercept
from tucows.models import Node, Edge, local_postgres_engine


@dataclass
class NodePair:
    start: str
    end: str


@dataclass
class Query:
    paths: Optional[NodePair]
    cheapest: Optional[NodePair]


@dataclass
class Queries(DataClassJsonMixin):
    queries: List[Query]


@dataclass
class NodePath:
    from_: str = field(metadata=config(field_name="from"))
    to: str
    paths: List[List[str]]


@dataclass(kw_only=True)
class Answer:
    paths: Optional[NodePath] = field(default=None, metadata=config(exclude=(lambda x: x is None)))
    cheapest: Optional[NodePath] = field(default=None, metadata=config(exclude=(lambda x: x is None)))


@dataclass
class QueriesResult(DataClassJsonMixin):
    answers: List[Answer]


@logger.catch
def query_main():
    engine = local_postgres_engine()
    queries: Queries = Queries.from_dict(json.load(sys.stdin), infer_missing=True)
    path_queries = []
    cheapest_queries = []

    for query in queries.queries:
        if query.paths:
            path_queries.append((query.paths.start, query.paths.end))
        if query.cheapest:
            cheapest_queries.append((query.cheapest.start, query.cheapest.end))

    result = QueriesResult([])
    with (Session(engine) as session):
        all_paths_database_query = build_database_query(path_queries, all_paths=True)

        endpoints = defaultdict(list)
        for from_node_id, to_node_id, node_path in session.execute(all_paths_database_query):
            path_endpoints = (from_node_id, to_node_id)
            endpoints[path_endpoints].append(node_path)

        for (from_node_id, to_node_id), node_paths in endpoints.items():
            result.answers.append(Answer(paths=NodePath(from_node_id, to_node_id, node_paths)))

    print(result.to_json())


def build_database_query(query_tuples, *, all_paths=None, cheapest_paths=None):
    if bool(all_paths) == bool(cheapest_paths):
        raise RuntimeError("Please specify one of all_paths or cheapest_paths")
    if all_paths:
        cheapest_paths = False

    sources = [s for s, _ in query_tuples]
    topq = select(
        Node.id.label("from_node_id"),
        Node.id.label("to_node_id"),
        literal(0).label("path_length"),
        literal(False).label("is_cycle"),
        array((Node.id,)).label("node_path"),
        array([]).cast(ARRAY(VARCHAR)).label("edge_path"),
        literal(0.0).label("cost")

    ).filter(Node.id.in_(sources)).cte('cte', recursive=True)
    bottomq = select(
        topq.c.from_node_id,
        Edge.to_node_id,
        topq.c.path_length + 1,
        Any(Edge.to_node_id, topq.c.node_path),
        topq.c.node_path + Edge.to_node_id,
        topq.c.edge_path + Edge.id,
        topq.c.cost + Edge.cost
    ).join(topq, Edge.from_node_id == topq.c.to_node_id)
    transitive_closure = topq.union(bottomq)
    if cheapest_paths:
        ranked_results = select(
            transitive_closure, rank().over(
                order_by=transitive_closure.c.cost,
                partition_by=(transitive_closure.c.from_node_id, transitive_closure.c.to_node_id)
            ).label("rank")
        ).subquery()

        final_query = select(ranked_results).where(ranked_results.c.rank == 1)
    else:
        final_query = select(transitive_closure)
    database_query = select(
        final_query.selected_columns.from_node_id,
        final_query.selected_columns.to_node_id,
        final_query.selected_columns.node_path
    ).where(final_query.selected_columns.path_length > 0
            , tuple_(final_query.selected_columns.from_node_id,
                     final_query.selected_columns.to_node_id).in_(query_tuples)
            )
    return database_query


if __name__ == '__main__':
    setup_loguru_logging_intercept()
    query_main()
