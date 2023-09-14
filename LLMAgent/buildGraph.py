from matplotlib import pyplot as plt
from xml.etree import ElementTree as ET
import matplotlib
matplotlib.use('TkAgg')


class Lane:
    def __init__(
            self, id: str, speed: float, length: float,
            raw_shape: str
    ) -> None:
        self.id = id
        self.speed = speed
        self.length = length
        self.shape = self.process_raw_shape(raw_shape)

    def process_raw_shape(self, raw_shape: str) -> [[float]]:
        raw_list = raw_shape.split(' ')
        shape = [list(map(float, p.split(','))) for p in raw_list]
        return shape

    def plot_self(self, color: str, alpha: float):
        plt.plot(
            list(zip(*self.shape))[0],
            list(zip(*self.shape))[1],
            color=color, alpha=alpha
        )


class Edge:
    def __init__(self, id: str, fromNode: str, toNode: str) -> None:
        self.id = id,
        self.fromNode = fromNode
        self.toNode = toNode
        self.lanes: dict[str, Lane] = {}
        self.next_edges: set[str] = set()
        self.length: float = 0
        self.freeFlowSpeed = 13.89

    def get_length(self) -> None:
        max_length = 0
        for lane in self.lanes.values():
            if lane.length > max_length:
                max_length = lane.length
        self.length = max_length
        self.capacity = 1800.0 * len(self.lanes)

    def plot_self(self, color: str, alpha: float) -> None:
        for lane in self.lanes.values():
            lane.plot_self(color, alpha)


class Junction:
    def __init__(self, id: str) -> None:
        self.id = id
        self.inEdges: set[Edge] = set()
        self.outEdges: set[Edge] = set()

    def calCap(self) -> float:
        jCap = 0
        nEdges = len(self.inEdges)
        for edge in self.inEdges:
            jCap += edge.capacity / nEdges

        return jCap


class Graph:
    def __init__(self) -> None:
        self.edges: dict[str, Edge] = {}
        self.junctions: dict[str, Junction] = {}

    def get_junction(self, jid: str):
        return self.junctions[jid]

    @property
    def validJunctions(self):
        invalidJunctions = set(
            ['9173', '4680', '4562', '4423', '4609']
        )
        return self.junctions.keys() - invalidJunctions

    def get_edge(self, eid: str):
        return self.edges[eid]

    def getEdgeByJunction(self, fnode: str, tnode: str):
        fj = self.get_junction(fnode)
        for edge in fj.outEdges:
            if edge.toNode == tnode:
                return edge
        raise ValueError(f'There is no edge between {fnode} and {tnode}.')

    def plot_self(self):
        for edge in self.edges.values():
            edge.plot_self('grey', 0.3)


def completeJunctions(graph: Graph):
    for ek, ev in graph.edges.items():
        fj = graph.get_junction(ev.fromNode)
        tf = graph.get_junction(ev.toNode)
        fj.outEdges.add(ev)
        tf.inEdges.add(ev)


def build_graph(file: str) -> Graph:
    graph = Graph()
    eTree = ET.parse(file)
    root = eTree.getroot()
    for child in root:
        if child.tag == 'edge':
            eid = child.attrib['id']
            if ':' not in eid:
                fromNode = child.attrib['from']
                toNode = child.attrib['to']
                edge = Edge(eid, fromNode, toNode)
                for gchild in child:
                    lid = gchild.attrib['id']
                    speed = float(gchild.attrib['speed'])
                    length = float(gchild.attrib['length'])
                    raw_shape = gchild.attrib['shape']
                    lane = Lane(
                        lid, speed, length, raw_shape)
                    edge.lanes[lid] = lane
                    edge.get_length()
                graph.edges[eid] = edge
            else:
                continue
        elif child.tag == 'junction':
            jid = child.attrib['id']
            if ':' not in jid:
                graph.junctions[jid] = Junction(jid)
        elif child.tag == 'connection':
            from_edge_id = child.attrib['from']
            to_edge_id = child.attrib['to']
            if ':' not in from_edge_id and ':' not in to_edge_id:
                from_edge = graph.get_edge(from_edge_id)
                from_edge.next_edges.add(to_edge_id)
            else:
                continue
        else:
            continue

    completeJunctions(graph)
    return graph
