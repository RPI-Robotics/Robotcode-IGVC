from launch import LaunchDescription
from launch.substitutions import  PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Declare args
    
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
    
    launch_led_bridge_node = Node(
        package='led_bridge',
        executable='led_bridge',
        name='led_bridge',
        output='screen',
    )

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

    # TODO since this relies on a pi to start up for the remote context, may need to delay this
    launch_imu_node = Node(
        package='adi_imu',
        executable='adi_imu_node',
        output='screen',
        parameters=[{
            "imu_device_name": "adis16475-2",
            "iio_context_string": "ip:'10.42.0.2'"
        }]
    )

    nodes = [
        launch_navsat_node,
        launch_led_bridge_node,
        launch_zed_node,
        launch_rplidar_node,
        launch_compass_bridge_node,
        launch_imu_node
    ]

    return LaunchDescription(nodes)
