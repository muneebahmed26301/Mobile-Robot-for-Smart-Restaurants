#!usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from robot_interfaces.msg import Error
from std_msgs.msg import String

class CameraLineFollow(Node):
    def __init__(self):
        super().__init__("clf_node")

        self.error_subscriber_ = self.create_subscription(Error, '/line_follow/error', self.error_callback, 10)
        self.turn_direction_subscriber_ = self.create_subscription(String, '/line_follow/turn_direction', self.turn_direction_callback, 10)
        self.junction_subscriber_ = self.create_subscription(String, '/line_follow/junction', self.junction_callback, 10)
        self.cmd_publisher_ = self.create_publisher(Twist, '/line_follow/cmd_vel', 10)

        # self.base_speed = 0.5
        # self.min_speed = 0.2
        # self.min_turn_speed , self.max_turn_speed = -5.0, 5.0
        # self.w = 1.1
        # self.kp, self.kd, self.ki = 5.0, 0.6, 0.0
        self.base_speed = 0.06 # max 0.15
        self.min_speed = 0.02 #0.02
        self.min_turn_speed , self.max_turn_speed = -0.4, 0.4
        self.w = 1.1
        self.kp, self.kd, self.ki = 0.4, 0.1, 0 # 0.45, 0.05

        self.prev_error, self.error_sum = 0.0, 0.0
        self.turn_direction = "None"
        self.junction = "Straight"

        self.get_logger().info("clf_node has been started")
    
    def turn_direction_callback(self, msg: String):
        self.turn_direction = msg.data
    
    def junction_callback(self, msg: String):
        self.junction = msg.data

    def error_callback(self, msg: Error):
        cmd_vel = Twist()
        cmd_vel.linear.x, cmd_vel.angular.z = self.ControlLoop(msg)
        if self.junction != "White":
            self.cmd_publisher_.publish(cmd_vel)
    
    def ControlLoop(self, msg: Error):
        if self.turn_direction == "Reverse":
            return 0.0, 0.4
        if self.junction != "Straight":
            self.error_sum = 0.0
        error = (msg.line_error + self.w * msg.angular_error) / (self.w + 1)
        vel_x = max(self.min_speed, self.base_speed * (1.0 - abs(error)))
        self.error_sum = max(-1.0, min(1.0, self.error_sum + error))
        omega_z = self.kp * error + self.kd * (error - self.prev_error) + self.ki * self.error_sum
        self.prev_error = error
        return vel_x, max(self.min_turn_speed, min(self.max_turn_speed, omega_z))

def main(args=None):
    rclpy.init(args=args)
    clf_node = CameraLineFollow()
    try:
        rclpy.spin(clf_node)
    except KeyboardInterrupt:
        clf_node.get_logger().info("Keyboard Interrupt, clf_node is shutting down")
    finally:
        clf_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
