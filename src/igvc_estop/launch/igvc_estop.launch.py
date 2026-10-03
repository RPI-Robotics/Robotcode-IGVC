from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.actions import DeclareLaunchArgument
from igvc_launch_utils.launch_helper import *


def generate_launch_description():
    use_sim_gpio = LaunchConfiguration("use_sim_gpio")
    
    twist_mux_config = get_config("igvc_estop", "twist_mux.yaml")
    
    launch_args = [
        DeclareLaunchArgument(
            "use_sim_gpio",
            default_value="false",
            description="Use sim GPIO topic instead of Jetson GPIO",
        )
    ]
    
    twist_mux_node = get_node(
        'twist_mux',
        'twist_mux',
        parameters=[twist_mux_config],
        remappings=[
            # twist_mux output topic -> controller cmd_vel input
            ("cmd_vel_out", "/bot_drive_controller/cmd_vel"),
        ]
    )
    
    igvc_estop_node = get_node(
        'igvc_estop',
        'igvc_estop_node',
        parameters=[{
            "use_sim_gpio": use_sim_gpio,
            "sim_gpio_topic": "/sim_gpio_estop",
            "gpio_pin": 27,
            "gpio_mode": "BCM",
            "active_high": True,

            "mechanical_estop_pin": 22,
            "mechanical_active_low": False,

            "latch": True,
            "poll_hz": 50.0,

            "lock_topic": "/emergency_stop_lock",
            "reset_topic": "/emergency_stop_reset",
        }],
    )

    return LaunchDescription([
        *launch_args,
        twist_mux_node,
        igvc_estop_node
    ])
