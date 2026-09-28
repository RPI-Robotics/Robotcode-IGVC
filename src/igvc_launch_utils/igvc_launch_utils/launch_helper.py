from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

def include(package, launch_file, **kwargs):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(package), '/launch/', *launch_file]),
        **kwargs
    )