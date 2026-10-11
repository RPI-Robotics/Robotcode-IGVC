from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node

from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch.event_handlers import OnProcessExit
from launch.actions import DeclareLaunchArgument, RegisterEventHandler

from launch.conditions import UnlessCondition

from igvc_launch_utils.launch_helper import *

def generate_launch_description():
    robot_controllers = get_config("igvc_hardware", "bot_controllers.yaml")
    
    use_sim = LaunchConfiguration("use_sim")
    
    # Declare args
    launch_args = [
        DeclareLaunchArgument(
            name="use_sim",
            default_value="false",
            description="Wether or not the robot is launching in simulation"
        )
    ]
    
    
    # Get nodes
    control_node = get_node("controller_manager", "ros2_control_node", 
        condition = UnlessCondition(use_sim),
        parameters=[robot_controllers], # TODO in the ODrive botwheel explorer example, the description contents are also passed in here.
        remappings=[("~/robot_description", "/robot_description"),], 
    )
    robot_controller_spawner = get_node("controller_manager", "spawner",
        arguments=["bot_drive_controller", "--controller-manager", "/controller_manager", "--switch-timeout", "20.0"],
        remappings=[('~/cmd_vel','/cmd_vel'), ("~/robot_description", "/robot_description")]
    )
    joint_state_broadcaster_spawner = get_node("controller_manager", "spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager", "--switch-timeout", "20.0"],
    )


    delay_robot_controller_spawner_after_joint_state_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[robot_controller_spawner],
        )
    )


    return LaunchDescription([
        *launch_args,
        control_node,
        joint_state_broadcaster_spawner,
        robot_controller_spawner
    ])
