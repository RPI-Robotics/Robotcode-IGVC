import os

from ament_index_python import get_package_share_directory
from launch import LaunchDescription, LaunchDescriptionSource
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import FrontendLaunchDescriptionSource, PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

def include(package, launch_file, **kwargs):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(package), '/launch/', launch_file]),
        **kwargs
    )

def generate_launch_description():
    use_sim = LaunchConfiguration('use_sim')
    use_mock_hardware = LaunchConfiguration('use_mock_hardware')
    sim_world = LaunchConfiguration('sim_world')
    use_slam = LaunchConfiguration('use_slam')
    use_nav = LaunchConfiguration('use_nav')
    
    launch_args = [
        DeclareLaunchArgument(
            'use_sim',
            default_value='false',
            description='Run in Simulation'
        ),
        DeclareLaunchArgument(
            'sim_world',
            default_value='track_v1',
            description='The name of the scenario to open in Gazebo'
        ),
        DeclareLaunchArgument(
            'use_mock_hardware',
            default_value=use_sim, # You are always mocking in simulation, but can specify if you need to bypass physical descriptors for testing
            description='Mocks all hardware'
        ),
        
        DeclareLaunchArgument(
            'use_slam',
            default_value='true', 
            description='Launch rtabmap for SLAM'
        ),
        DeclareLaunchArgument(
            'use_nav',
            default_value='true', 
            description='Launch Nav2'
        ),
    ]
    
    estop = include('igvc_estop', 'igvc_estop.launch.py', launch_arguments={'use_sim_gpio': use_sim}.items()),
    description = include('igvc_description', 'publisher.launch.py', launch_arguments={'use_mock_hardware': use_mock_hardware}.items()),
    simulation = include('igvc_gazebo', [sim_world, '.launch.py'], condition=IfCondition(use_sim)),
    control = include('igvc_hardware', 'control.launch.py'),
    real_hardware = include('igvc_hardware', 'hardware.launch.py', condition=UnlessCondition(use_mock_hardware)),
    slam = include('igvc_slam', 'dual_ekf.launch.py', condition=IfCondition(use_slam)),
    cv = include('igvc_cv', 'igvc_cv.launch.py'),
    nav = include('igvc_nav', 'igvc_nav.launch.py', condition=IfCondition(use_nav)),

    
    return LaunchDescription([
        *launch_args,
        estop,
        description,
        simulation,
        control,
        real_hardware,
        slam,
        cv,
        nav,
    ])
