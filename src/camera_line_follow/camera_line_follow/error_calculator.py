#!usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from std_msgs.msg import Bool
from robot_interfaces.msg import Error
import cv2
from cv_bridge import CvBridge
import numpy as np
import time

class ErrorCalculator(Node):
    def __init__(self):
        super().__init__("error_calculator")

        self.transform_img_subscriber_ = self.create_subscription(Image, '/camera/image_perspective_transform', self.img_callback, 10)
        self.turn_direction_subscriber_ = self.create_subscription(String, '/line_follow/turn_direction', self.turn_direction_callback, 10)
        self.is_line_publisher_ = self.create_publisher(Bool, '/line_follow/is_line', 10)
        self.error_publisher_ = self.create_publisher(Error, '/line_follow/error', 10)
        self.debug_img_publisher_ = self.create_publisher(Image, '/line_follow/error_debug_img', 10)
        self.br = CvBridge()

        self.slice = 75
        self.pad = 5
        self.edge_tolerance = 15
        self.min_area = 500
        self.max_points = 20
        self.turn_direction = "None"
        self.prev_error, self.prev_ang = 0.0, 0.0

        self.get_logger().info("error_calculator has been started")
    
    def img_callback(self, msg: Image):
        transform_img = self.br.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        error, ang = self.ComputeError(transform_img)
        error_msg = Error()
        error_msg.line_error = error
        error_msg.angular_error = ang
        self.error_publisher_.publish(error_msg)
    
    def turn_direction_callback(self, msg: String):
        self.turn_direction = msg.data
    
    def ComputeError(self, img):
        # Preprocessing
        is_line = False
        error, ang = self.prev_error, self.prev_ang
        img = img[self.slice:,:]
        thresh_img = self.RedMask(img)
        # self.debug_img_publisher_.publish(self.br.cv2_to_imgmsg(thresh_img, encoding='mono8'))
        # Find Largest Contour and Fit to Polygon
        contours, _ = cv2.findContours(thresh_img.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 0:
            largest_contour = max(contours, key=cv2.contourArea)
            height, width = img.shape[:2]
            if cv2.contourArea(largest_contour) > self.min_area:
                epsilon = 0.01 * cv2.arcLength(largest_contour, True)
                smoothed_contour = cv2.approxPolyDP(largest_contour, epsilon, True)
                filtered_contour = self.FilterContour(smoothed_contour, height, width)
                filtered_contour = self.AddTurnBias(filtered_contour, height, width)
                if len(filtered_contour) < self.max_points:
                    is_line = True
                    # Calculate Error and Angle
                    moments = cv2.moments(filtered_contour)
                    if moments['m00'] != 0:
                        cx = int(moments['m10'] / moments['m00'])
                        cy = int(moments['m01'] / moments['m00'])
                    else:
                        cx = width//2
                        cy = height//2
                    setpoint = width // 2
                    error = cx - setpoint
                    [vx, vy, x0, y0] = cv2.fitLine(filtered_contour, cv2.DIST_L2, 0, 0.01, 0.01)
                    slope = vy / vx
                    ang = np.arctan(slope) * 180 / np.pi
                    ang = ang.item()
                    if ang < 0:
                        ang = - 90 - ang
                    else:
                        ang = 90 - ang
                    # Debug Visuals
                    for point in filtered_contour:
                        cv2.circle(img, tuple(point[0]), 5, (255, 0, 0), -1)
                    x1 = int(x0 - vx * 1000)
                    y1 = int(y0 - vy * 1000)
                    x2 = int(x0 + vx * 1000)
                    y2 = int(y0 + vy * 1000)
                    cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.line(img, (setpoint, cy), (cx, cy), (0, 0, 255), 2)
                    cv2.putText(img, f"Error: {error}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    cv2.putText(img, f"Angle: {ang:.2f}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    self.debug_img_publisher_.publish(self.br.cv2_to_imgmsg(img, encoding='bgr8'))
                    # cv2.imshow("Debug Image", img)
                    # cv2.waitKey(1)
                    # Normalize and Return
                    error = -error / setpoint
                    ang = np.tanh(ang / 30)
                    error, ang = max(-1.0, min(1.0, error)), max(-1.0, min(1.0, ang))
                    self.prev_error, self.prev_ang = error, ang
        self.is_line_publisher_.publish(Bool(data=is_line))
        return error, ang

    def RedMask(self, img):
        hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Convert MATLAB-style [0,1] thresholds to OpenCV HSV scale
        # Hue is scaled to [0,179]; Saturation and Value to [0,255]
        h_min = int(0.934 * 179)
        h_max = int(0.046 * 179)
        # s_min = int(0.557 * 255)
        s_min = 0
        s_max = int(1.000 * 255)
        v_min = int(0.000 * 255)
        # v_max = int(0.800 * 255)
        v_max = 255
        # Create lower and upper bounds
        lower1 = np.array([0, s_min, v_min], dtype=np.uint8)
        upper1 = np.array([h_max, s_max, v_max], dtype=np.uint8)
        lower2 = np.array([h_min, s_min, v_min], dtype=np.uint8)
        upper2 = np.array([179, s_max, v_max], dtype=np.uint8)
        # Handle hue wrap-around with two masks
        mask1 = cv2.inRange(hsv_image, lower1, upper1)
        mask2 = cv2.inRange(hsv_image, lower2, upper2)
        thresh_img = cv2.bitwise_or(mask1, mask2)
        kernel = np.ones((5, 5), np.uint8)
        thresh_img = cv2.morphologyEx(thresh_img, cv2.MORPH_OPEN, kernel)
        thresh_img = cv2.morphologyEx(thresh_img, cv2.MORPH_CLOSE, kernel)
        return thresh_img
    
    def FilterContour(self, contour, height, width):
        if self.turn_direction == "None":
            # Handle Complexities when Line at Edge
            edge_point_count = 0
            edge_y_val = 0
            for point in contour:
                if point[0][0] >= width-self.edge_tolerance:
                    edge_point_count += 1
                    edge_y_val += point[0][1]
                elif point[0][0] <= self.edge_tolerance:
                    edge_point_count -= 1
                    edge_y_val += point[0][1]
            if edge_point_count >= 2:
                new_point = np.array([[[width, edge_y_val//edge_point_count]]], dtype=np.int32)
                contour = np.vstack((contour, new_point))
            elif edge_point_count <= -2:
                new_point = np.array([[[0, edge_y_val//abs(edge_point_count)]]], dtype=np.int32)
                contour = np.vstack((contour, new_point))
            return contour
        else:
            # Filter Contour based on Turn Direction
            filtered_contour = []
            for point in contour:
                x, y = point[0][0], point[0][1]
                if ((self.turn_direction == "Straight") and (width//16 <= x <= 15*width//16)) or \
                ((self.turn_direction == "Left") and (x <= 15*width//16) and (y >= height//16)) or \
                ((self.turn_direction == "Right") and (x >= width//16) and (y >= height//16)):
                    filtered_contour.append(point)
            if filtered_contour:
                return np.array(filtered_contour, dtype=np.int32)
            else:
                return contour
    
    def AddTurnBias(self, contour, height, width):
        # Add Points to make Turning Easier
        if self.turn_direction == "Straight":
            new_point = np.array([[[width//2, height]]], dtype=np.int32)
            contour = np.vstack((contour, new_point))
            new_point = np.array([[[width//2, 0]]], dtype=np.int32)
            contour = np.vstack((contour, new_point))
        elif self.turn_direction == "Left":
            new_point = np.array([[[width//2, height]]], dtype=np.int32)
            contour = np.vstack((contour, new_point))
            new_point = np.array([[[0, height//2]]], dtype=np.int32)
            contour = np.vstack((contour, new_point))
        elif self.turn_direction == "Right":
            new_point = np.array([[[width//2, height]]], dtype=np.int32)
            contour = np.vstack((contour, new_point))
            new_point = np.array([[[width, height//2]]], dtype=np.int32)
            contour = np.vstack((contour, new_point))
        return contour
    
def main(args=None):
    rclpy.init(args=args)
    error_calculator = ErrorCalculator()
    try:
        rclpy.spin(error_calculator)
    except KeyboardInterrupt:
        error_calculator.get_logger().info("Keyboard Interrupt, error_calculator is shutting down")
    finally:
        error_calculator.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
