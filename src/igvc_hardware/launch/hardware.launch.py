from launch import LaunchDescription

from igvc_launch_utils.launch_helper import *

def generate_launch_description(): 
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
    
    launch_navsat_node = get_node('ublox_gps', 'ublox_gps_node',
        name='navsat',
        parameters=[{
            "device" : "/dev/ttyUSB0",
            "uart1.baudrate" : 115200,
            "frame_id" : "navsat_link",
        }],
    )
    launch_led_bridge_node = get_node('led_bridge', 'led_bridge')
    launch_compass_bridge_node = get_node('compass_bridge', 'compass_bridge',
        parameters=[{
            "i2c_bus" : 7,
            "device_address" : 0x0E
        }],
    )
    
    return LaunchDescription([
        launch_navsat_node,
        launch_led_bridge_node,
        launch_zed_node,
        launch_rplidar_node,
        launch_compass_bridge_node
    ])
