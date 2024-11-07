from abc import ABC, abstractmethod
from typing import BinaryIO

from loguru import logger
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser

from tucows import input
from tucows.input import Graph


class InputProcessor(ABC):
    @abstractmethod
    def graph(self, graph: Graph):
        pass

    @abstractmethod
    def node(self, node: Graph.Nodes.Node):
        pass

    @abstractmethod
    def edge(self, edge: Graph.Edges.Edge):
        pass


def push_process_input(file_like: BinaryIO, input_processor: InputProcessor):
    xmlschema = etree.XMLSchema(file="tucows/input/graph.xsd")
    parser = XmlParser()
    try:
        graph_id = None
        graph_name = None
        graph_model = None
        context = etree.iterparse(file_like, events=("start", "end",), schema=xmlschema)
        context = iter(context)
        _, root = next(context)
        if root.tag != "graph":
            raise RuntimeError("Root element should be <graph>")

        for event, element in context:
            if event == "end":
                if element.tag == "id":
                    graph_id = element.text
                if element.tag == "name":
                    graph_name = element.text
                if graph_id and graph_name and not graph_model:
                    graph_model = Graph(graph_id, graph_name)
                    input_processor.graph(graph_model)

                if element.tag == "node":
                    if not graph_model:
                        raise RuntimeError("Model not defined yet")
                    node = parser.parse(element, input.Graph.Nodes.Node)
                    input_processor.node(node)

                if element.tag == "edge":
                    if not graph_model:
                        raise RuntimeError("Model not defined yet")
                    edge = parser.parse(element, input.Graph.Edges.Edge)
                    input_processor.edge(edge)
            root.clear()
    except etree.XMLSyntaxError as e:
        logger.exception("Error while parsing XML")
