from launch.actions import IncludeLaunchDescription, Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

def launch_file(package, launch_file, **kwargs):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(package), '/launch/', *launch_file]),
        **kwargs
    )
    
def node(package, executable, **kwargs):
    if 'name' not in kwargs.keys():
        kwargs['name'] = executable
    return Node(
        package=package,
        executable=executable,
        output="screen",
        **kwargs
    )
    
def config(package, config_file):
    return PathJoinSubstitution(
        FindPackageShare(package),
        "/config/",
        *config_file,
    )