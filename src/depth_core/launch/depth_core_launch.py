from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch_ros.actions import Node
import os

def generate_launch_description():
    astra_launch_path = os.path.join(
        os.getenv('COLCON_PREFIX_PATH').split(':')[0],
        'astra_camera', 'share', 'astra_camera', 'launch', 'astra.launch.xml'
    )

    return LaunchDescription([
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(astra_launch_path)
        ),

        Node(
            package='depth_core',
            executable='collision_avoider',
            name='collision_avoider',
            output='screen'
        )
    ])
