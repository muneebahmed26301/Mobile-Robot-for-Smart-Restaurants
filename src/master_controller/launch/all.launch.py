from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, GroupAction
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    use_sim = LaunchConfiguration('use_sim')
    serial_dev = LaunchConfiguration('serial_dev')
    video_dev = LaunchConfiguration('video_dev')

    return LaunchDescription([
        # Declare arguments
        DeclareLaunchArgument(
            'use_sim',
            default_value='true',
            description='Whether to use the simulator'
        ),
        DeclareLaunchArgument(
            'serial_dev',
            default_value='/dev/ttyUSB0',
            description='Serial device for micro-ROS agent'
        ),
        DeclareLaunchArgument(
            'video_dev',
            default_value='/dev/video2',
            description='Video device for v4l2_camera'
        ),

        # Conditionally launch the simulator
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(
                    FindPackageShare('my_bot').find('my_bot'),
                    'launch/launch_sim.launch.py'
                )
            ]),
            condition=IfCondition(use_sim),
            launch_arguments={'world': './src/my_bot/worlds/map2.world'}.items(),
        ),

        # Launch camera_line_follow
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(
                    FindPackageShare('camera_line_follow').find('camera_line_follow'),
                    'launch/launch_clf.py'
                )
            ])
        ),

        # Launch master_controller
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(
                    FindPackageShare('master_controller').find('master_controller'),
                    'launch/launch_master.py'
                )
            ])
        ),

        # Launch depth_core
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(
                    FindPackageShare('depth_core').find('depth_core'),
                    'launch/depth_core_launch.py'
                )
            ]),
            condition=UnlessCondition(use_sim),
        ),

        # Launch micro_ros_agent only if not using simulation
        ExecuteProcess(
            cmd=['ros2', 'run', 'micro_ros_agent', 'micro_ros_agent', 'serial', '--dev', serial_dev],
            condition=UnlessCondition(use_sim),
            output='screen'
        ),

        # Launch v4l2_camera_node only if not using simulation
        ExecuteProcess(
            cmd=[
                'ros2', 'run', 'v4l2_camera', 'v4l2_camera_node',
                '--ros-args',
                '-p', ['video_device:=', video_dev],
                # '--remap', '/image_raw:=/camera/image_raw'
            ],
            condition=UnlessCondition(use_sim),
            output='screen'
        ),
    ])
