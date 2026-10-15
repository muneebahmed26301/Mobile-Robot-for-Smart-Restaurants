import json
from master_controller.helper_classes.coordinates import Coordinates
from master_controller.helper_classes.graph_edge import GraphEdge

class GraphNode:
    def __init__(self, id: int = None, junction: str = None, junc_type: str = None, position: Coordinates = None, str_data: str = None):
        if str_data:
            data = json.loads(str_data)
            self.id = data["id"]
            self.junction = data["junction"]
            self.junc_type = data["junc_type"]
            self.position = Coordinates(str_data=data["position"])
            self.edges = [GraphEdge(str_data=json.dumps(e)) for e in data["edges"]]
        else:
            self.id = id
            self.junction = self.ConvertJunction(junction)
            self.junc_type = junc_type
            self.position = position
            self.edges = []
    
    def __repr__(self):
        return json.dumps({
            "id":self.id, 
            "junction":self.junction, 
            "junc_type":self.junc_type, 
            "position":repr(self.position), 
            "edges":[json.loads(repr(e)) for e in self.edges]
        })
    
    def ConvertJunction(self, junction: str):
        if junction in ["T", "T-Left", "T-Right"]:
            return "T"
        elif junction in ["Left", "Right"]:
            return "Turn"
        else:
            return junction
    
    def AddEdge(self, target_node_id: int, direction: Coordinates, weight: float):
        edge = GraphEdge(self.id, target_node_id, direction, weight)
        self.edges.append(edge)
        return edge
