from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='camera_line_follow',
            executable='clf_node',
            name='clf_node'
        ),
        Node(
            package='camera_line_follow',
            executable='image_processor',
            name='image_processor'
        ),
        Node(
            package='camera_line_follow',
            executable='junction_classifier',
            name='junction_classifier'
        ),
        Node(
            package='camera_line_follow',
            executable='error_calculator',
            name='error_calculator'
        ),
    ])
