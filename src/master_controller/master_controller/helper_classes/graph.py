import json
import networkx as nx
import matplotlib.pyplot as plt
from master_controller.helper_classes.coordinates import Coordinates
from master_controller.helper_classes.graph_node import GraphNode
from master_controller.helper_classes.graph_edge import GraphEdge

class Graph:
    def __init__(self, str_data: str = None):
        if str_data:
            data = json.loads(str_data)
            self.nodes = {int(id): GraphNode(str_data=json.dumps(n)) for id, n in data["nodes"].items()}
            self.edges = [GraphEdge(str_data=json.dumps(e)) for e in data["edges"]]
            self.special_nodes = {junc_type: int(id) for junc_type, id in data["special_nodes"].items()}
        else:
            self.nodes = {}
            self.edges = []
            self.special_nodes = {}
    
    def __repr__(self):
        return json.dumps({
            "nodes": {id: json.loads(repr(n)) for id, n in self.nodes.items()},
            "edges": [json.loads(repr(e)) for e in self.edges],
            "special_nodes": self.special_nodes
        })
    
    def SaveGraph(self, folder: str):
        filename = folder + '/graph3.json'
        with open(filename, "w") as file:
            file.write(repr(self))
        self.DrawGraph(folder)
    
    @staticmethod
    def LoadGraph(folder: str):
        filename = folder + '/graph3.json'
        with open(filename, "r") as file:
            graph_data = file.read()
        return Graph(graph_data)
    
    def AddNode(self, junction: str, junc_type: str = None, position = Coordinates(0, 0)):
        ids = self.nodes.keys()
        if len(ids) == 0:
            id = 0
        else:
            id = max(ids) + 1
        self.nodes[id] = GraphNode(id, junction, junc_type, position)
        if junc_type is not None:
            self.special_nodes[junc_type] = id
        return id
    
    def AddEdge(self, source_node_id: int, target_node_id: int, direction: Coordinates, weight: float = 1.0):
        source_node = self.nodes[source_node_id]
        target_node = self.nodes[target_node_id]
        edge1 = source_node.AddEdge(target_node_id, direction, weight)
        edge2 = target_node.AddEdge(source_node_id, -direction, weight)
        self.edges.append(edge1)
        self.edges.append(edge2)
    
    def EdgeExists(self, node_id: int, direction: Coordinates):
        for edge in self.edges:
            if node_id == edge.source_node_id and direction == edge.direction:
                return True
        return False
    
    def GetEdgeDirection(self, source_node_id: int, target_node_id: int):
        edges = self.nodes[source_node_id].edges
        for edge in edges:
            if target_node_id == edge.target_node_id:
                return edge.direction
        return None
    
    def FindPathBFS(self, source_node_id: int, target_node_id: int):
        queue = []
        explored = set()
        parent = {}
        queue.append(source_node_id)
        explored.add(source_node_id)
        while queue:
            node_id = queue.pop(0)
            if node_id == target_node_id:
                path = []
                current_node_id = target_node_id
                while current_node_id != source_node_id:
                    path.append(current_node_id)
                    current_node_id = parent[current_node_id]
                path.reverse()
                return path
            edges = self.nodes[node_id].edges
            for edge in edges:
                neighbour_id = edge.target_node_id
                if neighbour_id not in explored:
                    explored.add(neighbour_id)
                    parent[neighbour_id] = node_id
                    queue.append(neighbour_id)
        return None
    
    def DrawGraph(self, folder: str):
        node_info = {}
        current_position = Coordinates(0, 0)
        visited = set()
        node_info[0] = (current_position, "End", "Start")
        visited.add(0)
        queue = [0]
        while queue:
            node_id = queue.pop(0)
            if node_id not in node_info:
                continue
            edges = self.nodes[node_id].edges
            for edge in edges:
                neighbour_id = edge.target_node_id
                neighbour_node = self.nodes[neighbour_id]
                if neighbour_id not in visited:
                    node_info[neighbour_id] = (node_info[node_id][0] + edge.direction, neighbour_node.junction, neighbour_node.junc_type)
                    visited.add(neighbour_id)
                    queue.append(neighbour_id)
        
        G = nx.DiGraph()
        pos = {}
        labels = {}
        for node_id, (position, junction, junc_type) in node_info.items():
            pos[node_id] = (position.x, position.y)
            if junc_type:
                labels[node_id] = f"{junction} {junc_type} ({node_id})"
            else: 
                labels[node_id] = f"{junction} ({node_id})"
        edge_labels = {}
        for edge in self.edges:
            if edge.target_node_id > edge.source_node_id:
                G.add_edge(edge.source_node_id, edge.target_node_id)
                edge_labels[(edge.source_node_id, edge.target_node_id)] = f"{edge.direction}"
        plt.figure(figsize=(8, 6))
        nx.draw(G, pos, with_labels=True, labels=labels, node_size=700, node_color="lightblue", edge_color="gray", font_size=10)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red")
        save_path = folder + "/graph2.png"
        plt.savefig(save_path, format="PNG")
