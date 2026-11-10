from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument

from igvc_launch_utils.launch_helper import *
            
def generate_launch_description(): 
    
    # Declare args
  
    # should use /dev/serial/by-id/ or /dev/serial/by-path/ to avoid conflict with gps
    launch_args = [ DeclareLaunchArgument(
        'micro_ros_port',
        default_value='/dev/ttyUSB0', 
        description='serial device for micro-ROS'
    ),
      DeclareLaunchArgument(
            name='gps_port', 
            default_value='/dev/ttyUSB0', 
            description='path to serial port for GPS module'),
      DeclareLaunchArgument(
          name='enable_ntrip',
          default_value=False,
          description='whether to enable NTRIP functionality'),
      DeclareLaunchArgument(
          name='ntrip_user',
          default_value='user',
          description='username for NTRIP authentication'),
    ]
    
    micro_ros_arg = LaunchConfiguration('micro_ros_port')
    gps_port = LaunchConfiguration('gps_port')
    enable_ntrip = LaunchConfiguration('enable_ntrip')
    ntrip_user = LaunchConfiguration('ntrip_user')
    

    launch_zed_node = get_launch_file("zed_wrapper", 'zed_camera.launch.py',
        launch_arguments={
            'camera_model': 'zed2i',
            'publish_tf': 'false',
            'publish_urdf': 'false',
        }.items()
    )
    
    # Check here for published topics: https://www.stereolabs.com/docs/ros2/zed-node
    launch_rplidar_node = get_launch_file("rplidar_ros", 'rplidar_s2e_launch.py',
        launch_arguments={
            'udp_ip' : '10.42.0.5',
            'frame_id' : 'laser_frame'
        }.items()
    )
          
    launch_gps_node = get_launch_file('unicore_um982_driver', 'unicore.launch.py',
        parameters=[{
            "config_file" :  get_config('unicore_um982_driver',
            'unicore_driver_params.yaml'),
            "enable_ntrip" : enable_ntrip,
            "ntrip_user" : ntrip_user,
            "ntrip_pass" : "none",
            "gps_port" : gps_port
        }],  
    )
            
    launch_micro_ros_agent_node = get_node("micro_ros_agent", "micro_ros_agent",
        arguments = [
            'serial',
            '--dev', micro_ros_arg
        ],                                    
    )


    nodes = [
        *launch_args,
        launch_micro_ros_agent_node,
        launch_zed_node,
        launch_rplidar_node,
        launch_gps_node,
    ]
    return LaunchDescription(nodes)
