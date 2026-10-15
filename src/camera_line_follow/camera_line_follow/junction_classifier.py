#!usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from std_msgs.msg import Bool
from cv_bridge import CvBridge
import cv2
import numpy as np
from collections import deque, Counter

class JunctionClassifier(Node):
    def __init__(self):
        super().__init__("junction_classifier")

        self.transform_img_subscriber_ = self.create_subscription(
            Image, '/camera/image_perspective_transform', self.img_callback, 10)
        self.junction_publisher_ = self.create_publisher(String, '/line_follow/junction', 10)
        self.is_line_subscriber_ = self.create_subscription(
            Bool, '/line_follow/is_line', self.is_line_callback, 10)
        
        self.br = CvBridge()
        self.is_line = False

        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
        self.parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.parameters)

        self.mark_to_junc = {
            7: "T-Left",
            10: "Left",
            45: "Cross",
            24: "End"
        }

        self.prediction_window = deque(maxlen=5)
        self.last_pred = "Straight"
        self.last_publish_time = self.get_clock().now()
        self.last_seen_time = self.get_clock().now()

        self.end_delay = 1.5    # seconds to hold on to end junction
        self.other_delay = 0.5    # seconds to hold on to other junction

        self.get_logger().info("junction_classifier has been started")

    def img_callback(self, msg: Image):
        transform_img = self.br.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        thresh_img = self.BlueMask(transform_img)
        junc = self.ClassifyJunction(thresh_img)    
        # self.get_logger().info(f"Junction: {junc}")

        now = self.get_clock().now()
        time_since_last_seen = (now - self.last_seen_time).nanoseconds / 1e9

        if self.IsJunction(junc):
            self.last_pred = junc
            self.last_seen_time = now
            self.junction_publisher_.publish(String(data=junc))
        else:
            if (self.last_pred == "End"):
                if time_since_last_seen >= self.end_delay:
                    self.last_pred = junc
                    self.last_seen_time = now
                    self.junction_publisher_.publish(String(data=junc))
            else:
                if time_since_last_seen >= self.other_delay:
                    self.last_pred = junc
                    self.last_seen_time = now
                    self.junction_publisher_.publish(String(data=junc))

    def ClassifyJunction(self, img):
        corners, ids, _ = self.detector.detectMarkers(img)
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                if marker_id in self.mark_to_junc:
                    junction = self.mark_to_junc[marker_id]
                    if junction in ["Left", "T-Left"]:
                        c = corners[i][0]  # shape: (4,2)
                        vec = c[1] - c[0]
                        angle = np.arctan2(vec[1], vec[0]) * 180 / np.pi
                        if -45 <= angle <= 45:
                            return junction
                        elif -135 <= angle <= -45:
                            return "T" if junction == "T-Left" else "Right"
                        elif junction == "T-Left" and ((-180 <= angle <= -135) or (135 <= angle <= 180)):
                            return "T-Right"
                        else:
                            return self.last_pred
                    return junction
        return "Straight" if self.is_line else "White"

    def BlueMask(self, img):
        hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower = np.array([100, 0, 0], dtype=np.uint8)
        upper = np.array([130, 255, 255], dtype=np.uint8)
        thresh_img = cv2.inRange(hsv_image, lower, upper)
        kernel = np.ones((5, 5), np.uint8)
        thresh_img = cv2.morphologyEx(thresh_img, cv2.MORPH_OPEN, kernel)
        thresh_img = cv2.morphologyEx(thresh_img, cv2.MORPH_CLOSE, kernel)
        thresh_img = cv2.bitwise_not(thresh_img)
        cv2.imshow("Blue Mask", thresh_img)
        cv2.waitKey(1)
        return thresh_img
    
    def IsJunction(self, junction):
        return junction not in ["Straight", "White", "Ambiguous", "None"]

    def is_line_callback(self, msg: Bool):
        self.is_line = msg.data


def main(args=None):
    rclpy.init(args=args)
    junction_classifier = JunctionClassifier()
    try:
        rclpy.spin(junction_classifier)
    except KeyboardInterrupt:
        junction_classifier.get_logger().info("Keyboard Interrupt, junction_classifier is shutting down")
    finally:
        junction_classifier.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
