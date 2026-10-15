#!usr/bin/env python3
import rclpy
from rclpy.node import Node
from master_controller.helper_classes.coordinates import Coordinates
from master_controller.helper_classes.graph import Graph
from std_msgs.msg import String
from std_msgs.msg import Bool
from std_msgs.msg import Int8
import firebase_admin
from firebase_admin import credentials, firestore, db

class LineMapper(Node):
    def __init__(self):
        super().__init__("line_mapper")

        self.junction_subscriber_ = self.create_subscription(String, '/line_follow/junction', self.junction_callback, 10)
        self.should_map_line_subscriber_ = self.create_subscription(Bool, '/line_follow/should_map_line', self.should_map_line_callback, 10)
        self.turn_direction_publisher_ = self.create_publisher(String, '/line_follow/turn_direction', 10)
        self.is_map_completed_publisher_ = self.create_publisher(Bool, '/control/is_map_completed', 10)
        self.mode_publisher_ = self.create_publisher(Int8, '/control/mode', 10)
        self.timer_ = self.create_timer(0.1, self.timer_loop)

        self.should_map_line = False
        self.direction = Coordinates(0, 1)
        self.graph = Graph()
        self.graph.AddNode("End", "Start")
        self.prev_junction = "End"
        self.prev_node_id = 0
        self.current_node_id = 0
        self.unexplored_paths = []
        self.node_path = []
        self.table_count = 0
        self.kitchen_found = False
        self.is_map_completed = False

        cred_path = "/home/zakriya/raze/src/master_controller/creds/raze-2bd57-firebase-adminsdk-fbsvc-3fc39d7c98.json"
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://raze-2bd57-default-rtdb.firebaseio.com'
            })
        self.fs_db = firestore.client()

        self.get_logger().info("line_mapper has been started")
    
    def should_map_line_callback(self, msg: Bool):
        self.should_map_line = msg.data
    
    def junction_callback(self, msg: String):
        junction = msg.data
        if self.should_map_line:
            if self.prev_junction != junction:
                turn_msg = String()
                turn_msg.data = self.MapLineDFS(junction)
                self.turn_direction_publisher_.publish(turn_msg)
        if self.is_map_completed:
            turn_msg = String()
            turn_msg.data = self.BacktoStart(junction)
            self.turn_direction_publisher_.publish(turn_msg)
        self.prev_junction = junction
    
    def MapLineDFS(self, junction):
        turn_direction = "None"
        if not self.IsJunction(self.prev_junction) and self.IsJunction(junction):
            if not self.graph.EdgeExists(self.prev_node_id, self.direction):
                self.current_node_id = self.AddGraphNode(junction)
                self.graph.AddEdge(self.prev_node_id, self.current_node_id, self.direction)
                self.get_logger().info(f"{junction} added as Node with id {self.current_node_id}")
                self.get_logger().info(f"Node with id {self.prev_node_id} connected to {self.current_node_id} with direction {self.direction}")
                possible_turn_directions = self.GetTurnDirections(junction)
                for turn_dir in possible_turn_directions:
                    path_direction = self.GetPathDirection(turn_dir)
                    self.unexplored_paths.append([self.current_node_id, path_direction])
            self.prev_node_id = self.current_node_id
            if not self.node_path:
                if not self.unexplored_paths:
                    self.get_logger().info("line mapping completed successfully")
                    self.graph.SaveGraph("./src/master_controller/map")
                    self.is_map_completed = True
                    self.node_path = self.graph.FindPathBFS(self.current_node_id, 0)
                    next_node_id = self.node_path.pop(0)
                    new_direction = self.graph.GetEdgeDirection(self.current_node_id, next_node_id)
                    self.current_node_id = next_node_id   
                    turn_direction = self.GetTurnDirection(new_direction)
                    self.direction = new_direction
                    return turn_direction
                if self.unexplored_paths[-1][0] == self.current_node_id:
                    _, new_direction = self.unexplored_paths.pop()
                else:
                    self.node_path = self.graph.FindPathBFS(self.current_node_id, self.unexplored_paths[-1][0])
            if self.node_path:
                next_node_id = self.node_path.pop(0)
                new_direction = self.graph.GetEdgeDirection(self.current_node_id, next_node_id)
                self.current_node_id = next_node_id   
            turn_direction = self.GetTurnDirection(new_direction)
            self.direction = new_direction
        return turn_direction
    
    def BacktoStart(self, junction):
        turn_direction = "None"
        if not self.IsJunction(self.prev_junction) and self.IsJunction(junction):
            if self.current_node_id == 0:
                if self.direction == Coordinates(0, 1):
                    self.get_logger().info("reached start")
                    ref = db.reference("Modes/Value")
                    ref.set(-2)
                    self.mode_publisher_.publish(Int8(data=-2))
                    self.is_map_completed = False
                    return "None"
                else:
                    self.direction = Coordinates(0, 1)
                    return "Reverse"
            else:
                # if not self.node_path:
                #     self.node_path = self.graph.FindPathBFS(self.current_node_id, 0)
                if self.node_path:
                    next_node_id = self.node_path.pop(0)
                    new_direction = self.graph.GetEdgeDirection(self.current_node_id, next_node_id)
                    self.current_node_id = next_node_id   
                turn_direction = self.GetTurnDirection(new_direction)
                self.direction = new_direction
        return turn_direction
    
    def IsJunction(self, junction):
        return junction not in ["Straight", "White", "Ambiguous", "None"]
    
    def AddGraphNode(self, junction):
        if junction == "End":
            if self.table_count == 0 and not self.kitchen_found:
                self.kitchen_found = True
                return self.graph.AddNode(junction, "Kitchen")
            else:
                self.table_count += 1
                return self.graph.AddNode(junction, f"Table-{self.table_count}")
        else:
            return self.graph.AddNode(junction)
    
    def GetTurnDirections(self, junction):
        if junction == "End":
            return []
        elif junction == "Left":
            return ["Left"]
        elif junction == "Right":
            return ["Right"]
        elif junction == "T":
            return ["Right", "Left"]
        elif junction == "T-Left":
            return ["Straight", "Left"]
        elif junction == "T-Right":
            return ["Straight", "Right"]
        elif junction == "Cross":
            return ["Straight", "Right", "Left"]
    
    def GetPathDirection(self, turn_direction):
        if turn_direction == "Left":
            return Coordinates(-self.direction.y, self.direction.x)
        elif turn_direction == "Right":
            return Coordinates(self.direction.y, -self.direction.x)
        elif turn_direction == "Reverse":
            return -self.direction
        else:
            return self.direction
    
    def GetTurnDirection(self, path_direction: Coordinates):
        cross_prod = int(self.direction.CrossProduct(path_direction))
        if cross_prod == 1:
            return "Left"
        elif cross_prod == -1:
            return "Right"
        elif self.direction == -path_direction:
            return "Reverse"
        else:
            return "Straight"
    
    def timer_loop(self):
        self.is_map_completed_publisher_.publish(Bool(data=self.is_map_completed))

def main(args=None):
    rclpy.init(args=args)
    line_mapper = LineMapper()
    try:
        rclpy.spin(line_mapper)
    except KeyboardInterrupt:
        line_mapper.get_logger().info("Keyboard Interrupt, line_mapper is shutting down")
    finally:
        line_mapper.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
