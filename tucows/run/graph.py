import sys

import requests
from loguru import logger
from sqlalchemy.orm import Session

from tucows import models
from tucows.input import Graph
from tucows.input.processing import InputProcessor, push_process_input
from tucows.log import setup_loguru_logging_intercept
from tucows.models import local_postgres_engine


class DbInputProcessor(InputProcessor):

    def __init__(self, session: Session):
        self.session = session
        self.graph_model = None
        self.node_count = 0
        self.edge_count = 0

    def graph(self, graph: Graph):
        logger.info("Graph {}", graph)
        self.graph_model = models.Graph(graph.id, graph.name)
        self.session.add(self.graph_model)
        self.session.flush()

    # This assumes all nodes come before edges, as required by the exercise
    def node(self, node: Graph.Nodes.Node):
        logger.info("Node {}", node)
        self.session.add(models.Node(node.id, self.graph_model.id, node.name))
        self.node_count += 1
        if self.node_count % 1000 == 0:
            self.session.flush()

    def edge(self, edge: Graph.Edges.Edge):
        if self.edge_count == 0:
            self.session.flush()
        logger.info("Edge {}", edge)
        self.session.add(models.Edge(edge.id, self.graph_model.id, edge.from_value, edge.to, edge.cost or 0))
        self.edge_count += 1
        if self.edge_count % 1000 == 0:
            self.session.flush()


@logger.catch
def graph_consuming_main():
    engine = local_postgres_engine()

    uris = sys.argv[1:]

    with Session(engine) as session:
        input_processor = DbInputProcessor(session)

        for uri in uris:
            with requests.get(uri, stream=True).raw as file_like:
                push_process_input(file_like, input_processor)

        session.commit()


if __name__ == '__main__':
    setup_loguru_logging_intercept()
    graph_consuming_main()
