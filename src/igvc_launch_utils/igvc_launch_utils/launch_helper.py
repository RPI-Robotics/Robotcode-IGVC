from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution

def get_launch_file(package, launch_file, **kwargs):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(package), '/launch/', *launch_file]),
        **kwargs
    )
    
def get_node(package, executable, **kwargs):
    if 'name' not in kwargs.keys():
        kwargs['name'] = executable
    return Node(
        package=package,
        executable=executable,
        output="screen",
        **kwargs
    )
    
def get_config(package, config_file):
    return get_path(package, "config", config_file)
    
def get_path(package, folder, file):
    return PathJoinSubstitution([
        FindPackageShare(package),
        folder,
        file,
    ])