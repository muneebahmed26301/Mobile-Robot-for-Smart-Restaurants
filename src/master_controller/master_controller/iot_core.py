#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from std_msgs.msg import Int8
from std_msgs.msg import Bool
import firebase_admin
from firebase_admin import credentials, firestore, db
import base64
import os

class IOTCore(Node):
    def __init__(self):
        super().__init__("iot_core")

        self.mode_publisher_ = self.create_publisher(Int8, '/control/mode', 10)
        self.teleop_cmd_publisher_ = self.create_publisher(Twist, '/teleop/cmd_vel', 10)
        self.target_publisher_ = self.create_publisher(String, '/control/target', 10)
        self.is_map_completed_subscriber_ = self.create_subscription(Bool, '/control/is_map_completed', self.is_map_completed_callback, 10)
        self.is_target_reached_subscriber_ = self.create_subscription(Bool, '/control/is_target_reached', self.is_target_reached_callback, 10)
        self.timer_ = self.create_timer(1, self.timer_loop)
        
        # Initialize Firebase Admin SDK with both Firestore and Realtime Database
        cred_path = "/home/zakriya/raze/src/master_controller/creds/raze-2bd57-firebase-adminsdk-fbsvc-3fc39d7c98.json"
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://raze-2bd57-default-rtdb.firebaseio.com'
            })
        self.fs_db = firestore.client()
        self.is_target_reached = False
        self.is_map_completed = False
        self.map_online = False

        # image_path = "/home/zakriya/raze/src/master_controller/map/graph2.png"
        # self.upload_image_to_db(image_path)

        self.get_logger().info("iot_core has been started")
    
    def timer_loop(self):
        db_mode = self.get_mode_from_db()
        if db_mode == -1:
            teleop = self.get_teleop_from_db()
            self.teleop_cmd_publisher_.publish(teleop)
        elif db_mode == 2:
            target = self.get_target_from_db()
            if target and self.is_target_reached:
                self.target_publisher_.publish(String(data=target))
        self.mode_publisher_.publish(Int8(data=db_mode))

    def get_target_from_db(self):
        query = self.fs_db.collection('orders').order_by('timestamp')
        results = query.stream()
        for doc in results:
            data = doc.to_dict()
            table = data.get('table_no', 'N/A')
            status = data.get('status', 'N/A')
            if status == "Ready for Delivery":
                return "Kitchen"
            elif status == "Delivery in Process":
                return "Table-" + str(table)
        return None
    
    def get_mode_from_db(self):
        ref = db.reference("Modes/Value")
        db_mode = ref.get()
        return db_mode

    def get_teleop_from_db(self):
        ref1 = db.reference("controls/Ang_vel")
        ang_vel = ref1.get()
        ref2 = db.reference("controls/Lin_vel")
        lin_vel = ref2.get()
        teleop = Twist()
        if ang_vel:
            teleop.angular.z = float(ang_vel)
        else:
            teleop.angular.z = 0.0
        if lin_vel:
            teleop.linear.x = float(lin_vel)
        else:
            teleop.linear.x = 0.0
        return teleop

    def upload_image_to_db(self, image_path):
        try:
            if not os.path.exists(image_path):
                self.get_logger().warn(f"Image file '{image_path}' not found.")
                return
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            ref = db.reference("Stream/Image")
            ref.set(encoded_string)
            self.get_logger().info(f"Image '{image_path}' successfully uploaded to Firebase Realtime Database.")
        except Exception as e:
            self.get_logger().error(f"Error uploading image: {e}")
    
    def is_map_completed_callback(self, msg: Bool):
        self.is_map_completed = msg.data
        if not self.map_online and self.is_map_completed:
            self.map_online = True
            self.get_logger().info("Map completed, uploading image to Firebase")
            image_path = "/home/zakriya/raze/src/master_controller/map/graph2.png"
            self.upload_image_to_db(image_path)
    
    def is_target_reached_callback(self, msg: Bool):
        self.is_target_reached = msg.data

def main(args=None):
    rclpy.init(args=args)
    iot_core = IOTCore()
    try:
        rclpy.spin(iot_core)
    except KeyboardInterrupt:
        iot_core.get_logger().info("Keyboard Interrupt, iot_core is shutting down")
    finally:
        iot_core.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
