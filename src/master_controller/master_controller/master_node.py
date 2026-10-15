#!usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int8
from std_msgs.msg import String
from std_msgs.msg import Bool

class MasterController(Node):
    def __init__(self):
        super().__init__("master_node")

        self.clf_cmd_subscriber_ = self.create_subscription(Twist, '/line_follow/cmd_vel', self.clf_cmd_callback, 10)
        self.teleop_cmd_subscriber_ = self.create_subscription(Twist, '/teleop/cmd_vel', self.teleop_cmd_callback, 10)
        self.mode_subscriber_ = self.create_subscription(Int8, '/control/mode', self.mode_callback, 10)
        self.is_collision_possible_subscriber_ = self.create_subscription(Bool, '/control/is_collision_possible', self.collision_callback, 10)
        self.is_target_reached_subscriber_ = self.create_subscription(Bool, '/control/is_target_reached', self.is_target_reached_callback, 10)
        self.should_map_line_publisher_ = self.create_publisher(Bool, '/line_follow/should_map_line', 10)
        self.cmd_publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.motion_timer_ = self.create_timer(0.1, self.motion_loop)

        self.clf_cmd = Twist()
        self.teleop_cmd = Twist()
        self.motion_mode = -2
        self.cmd_type = ""
        self.is_collision_possible = False
        self.is_target_reached = False

        self.get_logger().info("master_node has been started")
    
    def InitializeRobotMode(self):
        if self.motion_mode == -2:
            # Stop Robot
            self.should_map_line_publisher_.publish(Bool(data=False))
            self.cmd_type = "STOP"
        elif self.motion_mode == -1:
            # Teleoperation
            self.should_map_line_publisher_.publish(Bool(data=False))
            self.cmd_type = "TELE"
        elif self.motion_mode == 0:
            # Just Simple Line Following
            self.should_map_line_publisher_.publish(Bool(data=False))
            self.cmd_type = "CLF"
        elif self.motion_mode == 1:
            # Explore and Map Environment (Line Following + Junction Handling + Mapping without SLAM)
            self.should_map_line_publisher_.publish(Bool(data=True))
            self.cmd_type = "CLF"
        elif self.motion_mode == 2:
            # Traverse Environment using Map (Line Following + Junction Handling + Path Planning without SLAM)
            self.should_map_line_publisher_.publish(Bool(data=False))
            if self.is_target_reached:
                self.cmd_type = "STOP"
            else:
                self.cmd_type = "CLF"
        elif self.motion_mode == 3:
            # Explore and Map Environment (Line Following + Junction Handling + Mapping with SLAM)
            self.should_map_line_publisher_.publish(Bool(data=False))
            self.cmd_type = "CLF"
        elif self.motion_mode == 4:
            # Traverse Environment using Map (Path Planning with SLAM)
            self.should_map_line_publisher_.publish(Bool(data=False))
            self.cmd_type = "SLAM"
        # Stop Robot if Collision is Possible
        if self.is_collision_possible:
            self.cmd_type = "STOP"
    
    def motion_loop(self):
        self.InitializeRobotMode()
        if self.cmd_type == "CLF":
            self.cmd_publisher_.publish(self.clf_cmd)
        elif self.cmd_type == "SLAM":
            pass
        elif self.cmd_type == "TELE":
            self.cmd_publisher_.publish(self.teleop_cmd)
        elif self.cmd_type == "STOP":
            cmd_vel = Twist()
            cmd_vel.linear.x, cmd_vel.angular.z = 0.0, 0.0
            self.cmd_publisher_.publish(cmd_vel)

    def clf_cmd_callback(self, msg: Twist):
        self.clf_cmd = msg
    
    def teleop_cmd_callback(self, msg: Twist):
        self.teleop_cmd = msg
    
    def mode_callback(self, msg: Int8):
        self.motion_mode = msg.data
    
    def collision_callback(self, msg: Bool):
        self.is_collision_possible = msg.data
    
    def is_target_reached_callback(self, msg: Bool):
        self.is_target_reached = msg.data

def main(args=None):
    rclpy.init(args=args)
    master_node = MasterController()
    try:
        rclpy.spin(master_node)
    except KeyboardInterrupt:
        master_node.get_logger().info("Keyboard Interrupt, master_node is shutting down")
    finally:
        master_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
