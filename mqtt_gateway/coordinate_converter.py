import numpy as np
from typing import Tuple, List


class CoordinateConverter:
  def __init__(
    self,
    source_origin: Tuple[float, float] = (0, 0),
    target_origin: Tuple[float, float] = (0, 0),
    rotation_angle: float = 0,  # in degrees
    scale_factor: float = 1.0,
    reflect_x: bool = False,
    reflect_y: bool = False,
  ):
    """
    Initialize a coordinate converter between two coordinate systems.

    Args:
        source_origin: Origin point (x,y) in the source coordinate system
        target_origin: Origin point (x,y) in the target coordinate system
        rotation_angle: Angle in degrees to rotate from source to target (counter-clockwise)
        scale_factor: Scaling factor from source to target (target = source * scale_factor)
        reflect_x: Whether to reflect across the x-axis
        reflect_y: Whether to reflect across the y-axis
    """
    self.source_origin = np.array(source_origin)
    self.target_origin = np.array(target_origin)
    self.rotation_angle = np.radians(rotation_angle)
    self.scale_factor = scale_factor
    self.reflect_x = reflect_x
    self.reflect_y = reflect_y

    # Pre-compute rotation matrix
    self.rotation_matrix = np.array(
      [
        [np.cos(self.rotation_angle), -np.sin(self.rotation_angle)],
        [np.sin(self.rotation_angle), np.cos(self.rotation_angle)],
      ]
    )

    # Pre-compute reflection matrix
    self.reflection_matrix = np.array(
      [[-1 if reflect_x else 1, 0], [0, -1 if reflect_y else 1]]
    )

  @classmethod
  def from_point_pairs(
    cls,
    source_points: List[Tuple[float, float]],
    target_points: List[Tuple[float, float]],
  ) -> "CoordinateConverter":
    """
    Create a coordinate converter from known point pairs in both systems.
    Requires at least two non-collinear points.

    Args:
        source_points: List of (x,y) coordinates in source system
        target_points: List of (x,y) coordinates in target system

    Returns:
        CoordinateConverter instance
    """
    if len(source_points) < 2 or len(target_points) < 2:
      raise ValueError("Need at least two points to determine transformation")
    if len(source_points) != len(target_points):
      raise ValueError("Number of source and target points must match")

    # Convert to numpy arrays
    source = np.array(source_points)
    target = np.array(target_points)

    # Calculate centroids (approximate origins)
    source_centroid = np.mean(source, axis=0)
    target_centroid = np.mean(target, axis=0)

    # Center the points
    centered_source = source - source_centroid
    centered_target = target - target_centroid

    # Calculate rotation angle using first two points
    v1_source = centered_source[1] - centered_source[0]
    v1_target = centered_target[1] - centered_target[0]

    # Calculate angle between vectors
    angle = np.arctan2(v1_target[1], v1_target[0]) - np.arctan2(
      v1_source[1], v1_source[0]
    )
    angle = np.degrees(angle)

    # Calculate scale factor
    source_dist = np.linalg.norm(v1_source)
    target_dist = np.linalg.norm(v1_target)
    scale = target_dist / source_dist

    # Determine if reflection is needed by checking the sign of the cross product
    cross_product = np.cross(v1_source, v1_target)
    reflect_x = cross_product < 0  # Negative cross product indicates reflection

    return cls(
      source_origin=tuple(source_centroid),
      target_origin=tuple(target_centroid),
      rotation_angle=angle,
      scale_factor=float(scale),
      reflect_x=bool(reflect_x),
    )

  def convert_point(self, point: Tuple[float, float]) -> Tuple[float, float]:
    """
    Convert a single point from source to target coordinate system.

    Args:
        point: (x,y) coordinates in source system

    Returns:
        (x,y) coordinates in target system
    """
    # Convert to numpy array
    np_point = np.array(point)

    # Translate to origin
    np_point = np_point - self.source_origin

    # Apply reflection
    np_point = np.dot(self.reflection_matrix, np_point)

    # Apply rotation
    np_point = np.dot(self.rotation_matrix, np_point)

    # Apply scaling
    np_point = np_point * self.scale_factor

    # Translate to target origin
    np_point = np_point + self.target_origin

    return tuple(np_point)

  def convert_points(
    self, points: List[Tuple[float, float]]
  ) -> List[Tuple[float, float]]:
    """
    Convert multiple points from source to target coordinate system.

    Args:
        points: List of (x,y) coordinates in source system

    Returns:
        List of (x,y) coordinates in target system
    """
    return [self.convert_point(point) for point in points]

  def inverse_convert_point(self, point: Tuple[float, float]) -> Tuple[float, float]:
    """
    Convert a single point from target to source coordinate system.

    Args:
        point: (x,y) coordinates in target system

    Returns:
        (x,y) coordinates in source system
    """
    # Convert to numpy array
    np_point = np.array(point)

    # Translate to origin
    np_point = np_point - self.target_origin

    # Apply inverse scaling
    np_point = np_point / self.scale_factor

    # Apply inverse rotation
    np_point = np.dot(self.rotation_matrix.T, np_point)

    # Apply inverse reflection (same as original reflection)
    np_point = np.dot(self.reflection_matrix, np_point)

    # Translate to source origin
    np_point = np_point + self.source_origin

    return tuple(np_point)

  def inverse_convert_points(
    self, points: List[Tuple[float, float]]
  ) -> List[Tuple[float, float]]:
    """
    Convert multiple points from target to source coordinate system.

    Args:
        points: List of (x,y) coordinates in target system

    Returns:
        List of (x,y) coordinates in source system
    """
    return [self.inverse_convert_point(point) for point in points]
