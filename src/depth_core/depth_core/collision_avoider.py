#!usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from ultralytics import YOLO
import logging
logging.getLogger("ultralytics").setLevel(logging.ERROR)
from sensor_msgs.msg import Image
from std_msgs.msg import Bool
from cv_bridge import CvBridge
import cv2
import numpy as np
import os

class CollisionAvoider(Node):
    def __init__(self):
        super().__init__("collision_avoider")

        self.depth_img_subscriber_ = self.create_subscription(Image, '/camera/depth/image_raw', self.depth_callback, 10)
        self.distance_debug_img_publisher_ = self.create_publisher(Image, '/control/distance_debug_img', 10)
        self.is_collision_possible_publisher_ = self.create_publisher(Bool, '/control/is_collision_possible', 10)
        self.br = CvBridge()

        self.model = YOLO("./src/depth_core/models/bestv2.pt")
        self.alpha = 1.5  # Contrast control
        self.beta = 30    # Brightness control
        self.distance_limit = 1.0  # Distance limit in meters
        
        self.get_logger().info("collision_avoider has been started")
    
    def depth_callback(self, msg):
        self.is_collision_possible = False
        depth_img = self.br.imgmsg_to_cv2(msg, desired_encoding='passthrough')
        input_img = self.preprocess_depth_image(depth_img)
        results = self.model.predict(input_img, imgsz=640, conf=0.6)
        annotated_img = results[0].plot()
        if results[0].boxes:
            for box in results[0].boxes.xyxy:
                x1, y1, x2, y2 = box.int().tolist()
            depth_crop = depth_img[y1:y2, x1:x2]
            depth_crop = depth_crop[depth_crop > 0]
            if len(depth_crop) > 0:
                distance = np.median(depth_crop) / 1000.0
            else:
                distance = float('inf')
            if distance < self.distance_limit:
                self.is_collision_possible = True
            cv2.putText(annotated_img, f"Distance: {distance}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(annotated_img, f"Collision: {self.is_collision_possible}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        self.distance_debug_img_publisher_.publish(self.br.cv2_to_imgmsg(annotated_img, encoding='bgr8'))
        self.is_collision_possible_publisher_.publish(Bool(data=self.is_collision_possible))
        # cv2.imshow("Collision Avoidance", annotated_img)
        # cv2.waitKey(1)
    
    def preprocess_depth_image(self, depth_img):
        # Normalize depth to 8-bit and adjust
        depth_8bit = cv2.convertScaleAbs(depth_img, alpha=(200.0 / max(0.0001, np.max(depth_img))))
        adjusted = cv2.convertScaleAbs(depth_8bit, alpha=self.alpha, beta=self.beta)
        # Convert to 3-channel by stacking (fake RGB)
        depth_rgb = cv2.cvtColor(adjusted, cv2.COLOR_GRAY2RGB)
        return depth_rgb

def main(args=None):
    rclpy.init(args=args)
    collision_avoider = CollisionAvoider()
    executor = MultiThreadedExecutor()
    executor.add_node(collision_avoider)
    try:
        executor.spin()
    except KeyboardInterrupt:
        collision_avoider.get_logger().info("Keyboard Interrupt, collision_avoider is shutting down")
    finally:
        collision_avoider.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
