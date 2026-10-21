import math
import struct
from typing import List, Tuple

import numpy as np
from sensor_msgs.msg import PointCloud2


def scale_uvs_to_cloud(
    image_uvs: List[Tuple[int, int]],
    image_w: int,
    image_h: int,
    cloud_w: int,
    cloud_h: int,
) -> List[Tuple[int, int]]:
    if image_w == cloud_w and image_h == cloud_h:
        return image_uvs

    sx = cloud_w / float(image_w)
    sy = cloud_h / float(image_h)

    cloud_uvs = []
    for u, v in image_uvs:
        cu = int(np.clip(u * sx, 0, cloud_w - 1))
        cv = int(np.clip(v * sy, 0, cloud_h - 1))
        cloud_uvs.append((cu, cv))

    return cloud_uvs


def read_cloud_points(
    cloud_msg: PointCloud2,
    uvs: List[Tuple[int, int]],
    min_range: float,
    max_range: float,
    max_abs: float,
    logger,
) -> List[Tuple[float, float, float]]:
    fields = {f.name: f.offset for f in cloud_msg.fields}
    if not all(k in fields for k in ("x", "y", "z")):
        logger.warn("PointCloud2 missing x/y/z fields")
        return []

    points = []

    for u, v in uvs:
        offset = v * cloud_msg.row_step + u * cloud_msg.point_step

        try:
            x = struct.unpack_from("f", cloud_msg.data, offset + fields["x"])[0]
            y = struct.unpack_from("f", cloud_msg.data, offset + fields["y"])[0]
            z = struct.unpack_from("f", cloud_msg.data, offset + fields["z"])[0]
        except Exception:
            continue

        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
            continue

        r = math.sqrt(x * x + y * y + z * z)
        if r < min_range or r > max_range:
            continue

        if abs(x) > max_abs or abs(y) > max_abs or abs(z) > max_abs:
            continue

        points.append((x, y, z))

    return points
