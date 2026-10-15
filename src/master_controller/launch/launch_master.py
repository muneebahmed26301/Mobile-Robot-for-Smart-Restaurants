from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='master_controller',
            executable='master_node',
            name='master_node'
        ),
        Node(
            package='master_controller',
            executable='line_mapper',
            name='line_mapper'
        ),
        Node(
            package='master_controller',
            executable='line_planner',
            name='line_planner'
        ),
        Node(
            package='master_controller',
            executable='motor_controller',
            name='motor_controller'
        ),
        Node(
            package='master_controller',
            executable='iot_core',
            name='iot_core'
        )
    ])
