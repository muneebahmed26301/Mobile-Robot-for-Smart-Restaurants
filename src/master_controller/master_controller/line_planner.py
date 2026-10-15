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

class LinePlanner(Node):
    def __init__(self):
        super().__init__("line_planner")

        self.junction_subscriber_ = self.create_subscription(String, '/line_follow/junction', self.junction_callback, 10)
        self.target_subscriber_ = self.create_subscription(String, '/control/target', self.target_callback, 10)
        self.turn_direction_publisher_ = self.create_publisher(String, '/line_follow/turn_direction', 10)
        self.mode_publisher_ = self.create_publisher(Int8, '/control/mode', 10)
        self.is_target_reached_publisher_ = self.create_publisher(Bool, '/control/is_target_reached', 10)
        self.timer_ = self.create_timer(0.1, self.timer_loop)

        self.direction = Coordinates(0, 1)
        self.graph = Graph()
        self.prev_junction = "End"
        self.prev_node_id = 0
        self.current_node_id = 0
        self.node_path = []
        self.target_junc_type = ""
        self.target_id = None
        self.is_target_reached = True

        cred_path = "/home/zakriya/raze/src/master_controller/creds/raze-2bd57-firebase-adminsdk-fbsvc-3fc39d7c98.json"
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://raze-2bd57-default-rtdb.firebaseio.com'
            })
        self.fs_db = firestore.client()

        # self.graph = Graph.LoadGraph("./src/master_controller/map")
        # self.graph.SaveGraph("./src/master_controller/map")

        self.get_logger().info("line_planner has been started")
    
    def target_callback(self, msg: String):
        if not self.target_id:
            self.target_junc_type = str(msg.data)
            self.graph = Graph.LoadGraph("./src/master_controller/map")
            self.target_id = self.graph.special_nodes[self.target_junc_type]
            self.is_target_reached = False
            self.get_logger().info(f"target set as {self.target_junc_type.lower()}")
            self.node_path = self.graph.FindPathBFS(self.current_node_id, self.target_id)
            self.get_logger().info(f"{self.node_path}")
            next_node_id = self.node_path.pop(0)
            new_direction = self.graph.GetEdgeDirection(self.current_node_id, next_node_id)
            self.current_node_id = next_node_id   
            turn_direction = self.GetTurnDirection(new_direction)
            self.direction = new_direction
            self.turn_direction_publisher_.publish(String(data=turn_direction))
        else:
            t = str(msg.data)
            id = self.graph.special_nodes[t]
            if id != self.target_id:
                self.target_junc_type = t
                self.target_id = id
                self.is_target_reached = False
                self.node_path = []
                self.get_logger().info(f"target set as {self.target_junc_type.lower()}")
                self.node_path = self.graph.FindPathBFS(self.current_node_id, self.target_id)
                self.get_logger().info(f"{self.node_path}")
                next_node_id = self.node_path.pop(0)
                new_direction = self.graph.GetEdgeDirection(self.current_node_id, next_node_id)
                self.current_node_id = next_node_id   
                turn_direction = self.GetTurnDirection(new_direction)
                self.direction = new_direction
                self.turn_direction_publisher_.publish(String(data=turn_direction))
    
    def junction_callback(self, msg: String):
        junction = msg.data
        if self.target_id and not self.is_target_reached:
            if self.prev_junction != junction:
                turn_msg = String()
                turn_msg.data = self.PlanPath(junction)
                self.turn_direction_publisher_.publish(turn_msg)
        self.prev_junction = junction
    
    def PlanPath(self, junction):
        turn_direction = "None"
        if not self.IsJunction(self.prev_junction) and self.IsJunction(junction):
            self.get_logger().info(f"{self.node_path} {self.current_node_id} {self.target_id}")
            if self.current_node_id == self.target_id:
                self.get_logger().info(f"reached {self.target_junc_type.lower()}")
                # ref = db.reference("Modes/Value")
                # ref.set(-2)
                # self.mode_publisher_.publish(Int8(data=-2))
                self.is_target_reached = True
                return "None"
            # if not self.node_path:
            #     self.node_path = self.graph.FindPathBFS(self.current_node_id, self.target_id)
            #     self.get_logger().info(f"{self.node_path}")
            if self.node_path:
                next_node_id = self.node_path.pop(0)
                new_direction = self.graph.GetEdgeDirection(self.current_node_id, next_node_id)
                self.current_node_id = next_node_id   
            turn_direction = self.GetTurnDirection(new_direction)
            self.direction = new_direction
        return turn_direction
    
    def IsJunction(self, junction):
        return junction not in ["Straight", "White", "Ambiguous"]
    
    def GetTurnDirection(self, path_direction: Coordinates):
        self.get_logger().info(f"{self.direction}, {path_direction}")
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
        self.is_target_reached_publisher_.publish(Bool(data=self.is_target_reached))

def main(args=None):
    rclpy.init(args=args)
    line_planner = LinePlanner()
    try:
        rclpy.spin(line_planner)
    except KeyboardInterrupt:
        line_planner.get_logger().info("Keyboard Interrupt, line_planner is shutting down")
    finally:
        line_planner.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
