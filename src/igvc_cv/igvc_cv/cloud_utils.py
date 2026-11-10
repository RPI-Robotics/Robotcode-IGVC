import numpy as np
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2


def cloud_to_xyz_matrix(cloud_msg: PointCloud2) -> np.ndarray:
    """Return an (H, W, 3) array where [i][j] is the XYZ point at pixel row i, column j."""
    pts = point_cloud2.read_points(
        cloud_msg,
        field_names=("x", "y", "z"),
        skip_nans=False,
        reshape_organized_cloud=True,
    )
    return np.stack([pts["x"], pts["y"], pts["z"]], axis=-1).astype(np.float32)
