#!usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32MultiArray
import time
import math

class MotorController(Node):
    def __init__(self):
        super().__init__("motor_controller")

        self.cmd_vel_subscriber_ = self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.enc_ticks_subscriber_ = self.create_subscription(Int32MultiArray, '/control/encoder_ticks', self.enc_ticks_callback, 10)
        self.pwm_publisher_ = self.create_publisher(Twist, '/control/pwm', 1)
        self.motion_timer_ = self.create_timer(0.2, self.motion_loop)

        self.wheel_radius = 0.135
        self.robot_width = 0.7
        self.ticks_per_rev = 785.0
        self.kp = 54 #54
        self.kd = 14 #14
        self.ki = 0.0
        self.prev_err = [0.0, 0.0, 0.0, 0.0]
        self.err_sum = [0.0, 0.0, 0.0, 0.0]
        self.prev_time = [time.time()] * 4
        self.enc_ticks = [0, 0, 0, 0]
        self.prev_enc_ticks = [0, 0, 0, 0]
        self.prev_pwm = [0.0, 0.0, 0.0, 0.0]
        self.cmd = Twist()
        
        self.get_logger().info("motor_controller has been started")
    
    def enc_ticks_callback(self, msg: Int32MultiArray):
        self.prev_enc_ticks = self.enc_ticks
        self.enc_ticks = list(msg.data)

    def cmd_vel_callback(self, msg: Twist):
        self.cmd = msg
    
    def motion_loop(self):
        pwm = self.ControlLoop(self.cmd.linear.x, self.cmd.angular.z)
        # pwm = self.Interpolate(pwm)
        self.prev_pwm = pwm
        pwm_msg = Twist()
        pwm_msg.linear.x = pwm[0]
        pwm_msg.linear.y = pwm[1]
        pwm_msg.angular.x = pwm[2]
        pwm_msg.angular.y = pwm[3]
        self.pwm_publisher_.publish(pwm_msg)
    
    def ControlLoop(self, vel_x, omega_z):
        left_wheel_ang_vel = (vel_x / self.wheel_radius) - ((self.robot_width / 2) * (omega_z / self.wheel_radius))
        right_wheel_ang_vel = (vel_x / self.wheel_radius) + ((self.robot_width / 2) * (omega_z / self.wheel_radius))
        # self.get_logger().info(f"Target Left Ang Vel {left_wheel_ang_vel} Target Right Ang Vel {right_wheel_ang_vel}")
        pwm = []
        for i in range(4):
            curr_time = time.time()
            dt = curr_time - self.prev_time[i]
            self.prev_time[i] = curr_time
            curr_ang_vel = 2 * math.pi * ((self.enc_ticks[i] - self.prev_enc_ticks[i]) / self.ticks_per_rev) / dt
            # self.get_logger().info(f"motor {i} current ang vel {curr_ang_vel}")
            error = (left_wheel_ang_vel - curr_ang_vel) if (i < 2) else (right_wheel_ang_vel - curr_ang_vel)
            if -0.0001 <= error <= 0.0001 and curr_ang_vel == 0:
                pwm.append(0.0)
                continue
            gain = self.kp * error + self.kd * (error - self.prev_err[i]) / dt + self.ki * self.err_sum[i]
            self.err_sum[i] += error
            self.prev_err[i] = error
            pwm.append(float(min(max(self.prev_pwm[i] + gain, -255), 255)))
        return pwm
    
    def Interpolate(self, pwm):
        for i in range(4):
            pwm[i] += (pwm[i] - self.prev_pwm[i]) * 0.75
            pwm[i] = float(min(max(pwm[i], -255), 255))
        return pwm

def main(args=None):
    rclpy.init(args=args)
    motor_controller = MotorController()
    try:
        rclpy.spin(motor_controller)
    except KeyboardInterrupt:
        motor_controller.get_logger().info("Keyboard Interrupt, motor_controller is shutting down")
    finally:
        motor_controller.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
