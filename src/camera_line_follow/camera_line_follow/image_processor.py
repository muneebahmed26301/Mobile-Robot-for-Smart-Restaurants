#!usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge
import numpy as np

class ImageProcessor(Node):
    def __init__(self):
        super().__init__("image_processor")

        self.raw_img_subscriber_ = self.create_subscription(Image, '/image_raw', self.img_callback, 10)
        self.transform_img_publisher_ = self.create_publisher(Image, '/camera/image_perspective_transform', 10)
        self.br = CvBridge()

        self.get_logger().info("image_processor has been started")
    
    def img_callback(self, msg: Image):
        raw_img = self.br.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        raw_img = cv2.flip(raw_img, -1)
        warped_img = self.PerspectiveTransform(raw_img)
        self.transform_img_publisher_.publish(self.br.cv2_to_imgmsg(warped_img, encoding='bgr8'))
    
    def PerspectiveTransform(self, img):
        height, width = img.shape[:2]
        # src_points = np.float32([
        #     [5*width//16-20, 11*height//16],     # top-left point
        #     [0, height],                         # bottom-left point
        #     [11*width//16+20, 11*height//16],    # top-right point
        #     [width, height],                     # bottom-right point  
        # ])
        src_points = np.float32([
            [5*width//16-50, height//2],     # top-left point
            [0, height],                         # bottom-left point
            [11*width//16+50, height//2],    # top-right point
            [width, height],                     # bottom-right point  
        ])
        output_size = (200, 200)
        dst_points = np.float32([
            [0, 0],                      # top-left point
            [0, 200],                 # bottom-left point
            [200, 0],                  # top-right point
            [200, 200],             # bottom-right point  
        ])

        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        warped_img = cv2.warpPerspective(img, matrix, output_size)

        # display_img = img.copy()
        # for point in src_points:
        #     point = tuple(map(int, point))
        #     cv2.circle(display_img, point, 5, (0, 255, 255), -1)
        # cv2.imshow("Raw Image", display_img)
        # cv2.imshow("Warped Image", warped_img)
        # cv2.waitKey(1)

        return warped_img

def main(args=None):
    rclpy.init(args=args)
    image_processor = ImageProcessor()
    try:
        rclpy.spin(image_processor)
    except KeyboardInterrupt:
        image_processor.get_logger().info("Keyboard Interrupt, image_processor is shutting down")
    finally:
        image_processor.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
