from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from igvc_launch_utils.launch_helper import *

def generate_launch_description():
    world = LaunchConfiguration('world')

    default_world = get_path('igvc_gazebo', 'worlds', 'empty_world.sdf')
    
    bridge_params = get_config('igvc_gazebo', 'gz_bridge.yaml')

    launch_args = [
        DeclareLaunchArgument(
            'world',
            default_value=default_world,
            description='World to load'
        ) 
    ]

    gazebo = get_launch_file(
        'ros_gz_sim', 
        'gz_sim.launch.py', 
        launch_arguments={'gz_args': ['-r -v4 ', world], 'on_exit_shutdown': 'true'}.items()
    )

    spawn_entity = get_node(
        'ros_gz_sim', 
        'create', 
        arguments=['-topic', 'robot_description', '-name', 'igvc_robot']
    )
    
    ros_gz_bridge = get_node(
        "ros_gz_bridge",
        "parameter_bridge", 
        arguments=['--ros-args', '-p', f'config_file:={bridge_params}']
    )
    
    return LaunchDescription([
        *launch_args,
        gazebo,
        spawn_entity,
        ros_gz_bridge
    ])
