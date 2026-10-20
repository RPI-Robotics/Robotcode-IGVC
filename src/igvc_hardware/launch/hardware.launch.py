from launch import LaunchDescription
from launch.substitutions import  PathJoinSubstitution
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

IMU_NAME = "TODO" # TODO

def generate_launch_description():
    # Declare args
    
    #lowk unnecessary, but allows other ports in testing 
    micro_ros_argument = DeclareLaunchArgument(
        'micro_ros_port',
        default_value='/dev/ttyUSB0', 
        description='serial device for micro-ROS'
    )
    
    #assuming baud rates match, which they should
    launch_micro_ros_agent = Node(
        package='micro_ros_agent',
        executable='micro_ros_agent',
        name='micro_ros_agent',
        output='screen',
        arguments=[
            'serial',
            '--dev', LaunchConfiguration('micro_ros_port')
        ]
    )
        
    launch_navsat_node = Node(
        package='ublox_gps',
        executable='ublox_gps_node',
        name='navsat',
        output='screen',
        parameters=[{
            "device" : "/dev/ttyUSB0",
            "uart1.baudrate" : 115200,
            "frame_id" : "navsat_link",
        }],
    )
    
    # no longer necessary
    #launch_led_bridge_node = Node(
    #    package='led_bridge',
    #    executable='led_bridge',
    #    name='led_bridge',
    #    output='screen',
    #)

    launch_zed_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("zed_wrapper"),
             '/launch',
             '/zed_camera.launch.py']
        ),
        launch_arguments={
            'camera_model': 'zed2i',
            'publish_tf': 'false',
            'publish_urdf': 'false',
        }.items()
    )
    # Check here for published topics: https://www.stereolabs.com/docs/ros2/zed-node
    
    launch_rplidar_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("rplidar_ros"),
             '/launch',
             '/rplidar_s2e_launch.py']
        ),
        launch_arguments={
            'udp_ip' : '10.42.0.5',
            'frame_id' : 'laser_frame'
        }.items()
    )

    launch_compass_bridge_node = Node(
        package='compass_bridge',
        executable='compass_bridge',
        name='compass_bridge',
        output='screen',
        parameters=[{
            "i2c_bus" : 7,
            "device_address" : 0x0E
        }],
    )

    nodes = [
        micro_ros_argument,
        launch_micro_ros_agent,
        launch_navsat_node,
        launch_zed_node,
        launch_rplidar_node,
        launch_compass_bridge_node
    ]

    return LaunchDescription(nodes)
