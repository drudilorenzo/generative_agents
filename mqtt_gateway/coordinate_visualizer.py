import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional
from .coordinate_converter import CoordinateConverter
import os

class CoordinateVisualizer:
    def __init__(self, converter: CoordinateConverter, background_image_path: Optional[str] = None):
        """
        Initialize the coordinate visualizer.

        Args:
            converter: CoordinateConverter instance to use for transformations
            background_image_path: Optional path to a background image to display
        """
        self.converter = converter
        self.original_image = None
        self.transformed_image = None
        
        if background_image_path:
            self.original_image = plt.imread(background_image_path)
            self.transformed_image = self._transform_image(self.original_image)

    def _transform_image(self, image: np.ndarray) -> np.ndarray:
        """
        Transform the image using the inverse of the stored coordinate converter.
        This maps from target space back to source space to avoid holes in the output.
        
        Args:
            image: Input image to transform
            
        Returns:
            Transformed image
        """
        # Get image dimensions
        height, width = image.shape[:2]
        
        # Calculate the bounds of the transformed coordinates by transforming the corners
        corners = np.array([
            [0, 0],
            [width, 0],
            [0, height],
            [width, height]
        ])
        transformed_corners = np.array([self.converter.convert_point((x, y)) for x, y in corners])
        
        # Calculate the bounds of the transformed coordinates
        min_x = np.min(transformed_corners[:, 0])
        max_x = np.max(transformed_corners[:, 0])
        min_y = np.min(transformed_corners[:, 1])
        max_y = np.max(transformed_corners[:, 1])
        
        # Calculate new dimensions that will fit all transformed coordinates
        new_width = int(np.ceil(max_x - min_x))
        new_height = int(np.ceil(max_y - min_y))
        
        # Create output image with new dimensions
        output_shape = (new_height, new_width, image.shape[2]) if len(image.shape) == 3 else (new_height, new_width)
        transformed_image = np.zeros(output_shape, dtype=image.dtype)
        
        # Create coordinate grid for the output space
        y, x = np.mgrid[0:new_height, 0:new_width]
        output_coords = np.stack([x.flatten() + min_x, y.flatten() + min_y], axis=1)
        
        # Transform coordinates using inverse transformation
        source_coords = np.array([self.converter.inverse_convert_point((x, y)) for x, y in output_coords])
        
        # Reshape back to image dimensions
        source_x = source_coords[:, 0].reshape(new_height, new_width)
        source_y = source_coords[:, 1].reshape(new_height, new_width)
        
        # Create mask for valid coordinates
        valid_mask = (
            (source_x >= 0) & (source_x < width) &
            (source_y >= 0) & (source_y < height)
        )
        
        # Use nearest neighbor interpolation for valid coordinates
        source_x = np.clip(source_x, 0, width-1).astype(int)
        source_y = np.clip(source_y, 0, height-1).astype(int)
        
        if len(image.shape) == 3:
            for c in range(image.shape[2]):
                # Only copy pixels from valid coordinates
                transformed_image[..., c] = np.where(
                    valid_mask,
                    image[source_y, source_x, c],
                    0  # Set out-of-bounds pixels to 0
                )
        else:
            transformed_image = np.where(
                valid_mask,
                image[source_y, source_x],
                0  # Set out-of-bounds pixels to 0
            )
            
        return transformed_image

    def plot_coordinate_transformation(
        self,
        source_points: List[Tuple[float, float]],
        target_points: Optional[List[Tuple[float, float]]] = None,
        title: str = "Coordinate Transformation",
        figsize: Tuple[int, int] = (12, 6)
    ):
        """
        Plot source points and their transformed coordinates with transformed image.

        Args:
            source_points: List of points in source coordinate system
            target_points: Optional list of expected target points for verification
            title: Plot title
            figsize: Figure size (width, height)
        """
        # Create figure with two subplots side by side
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # Plot source coordinates
        ax1.set_title("Source Coordinates")
        if self.original_image is not None:
            ax1.imshow(self.original_image)
        ax1.scatter(*zip(*source_points), c='blue', label='Source Points')
        ax1.grid(True)
        ax1.legend()

        # Plot target coordinates
        ax2.set_title("Target Coordinates")
        if self.transformed_image is not None:
            ax2.imshow(self.transformed_image)
        transformed_points = self.converter.convert_points(source_points)
        ax2.scatter(*zip(*transformed_points), c='red', label='Transformed Points')
        if target_points:
            ax2.scatter(*zip(*target_points), c='green', marker='x', label='Expected Points')
        ax2.grid(True)
        ax2.legend()

        # Add connecting lines between corresponding points
        for src, tgt in zip(source_points, transformed_points):
            ax1.plot([src[0]], [src[1]], 'bo')
            ax2.plot([tgt[0]], [tgt[1]], 'ro')

        plt.suptitle(title)
        plt.tight_layout()
        return fig

    def plot_inverse_transformation(
        self,
        target_points: List[Tuple[float, float]],
        source_points: Optional[List[Tuple[float, float]]] = None,
        title: str = "Inverse Coordinate Transformation",
        figsize: Tuple[int, int] = (12, 6)
    ):
        """
        Plot target points and their inverse transformed coordinates with transformed image.

        Args:
            target_points: List of points in target coordinate system
            source_points: Optional list of expected source points for verification
            title: Plot title
            figsize: Figure size (width, height)
        """
        # Create figure with two subplots side by side
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # Plot target coordinates
        ax1.set_title("Target Coordinates")
        if self.transformed_image is not None:
            ax1.imshow(self.transformed_image)
        ax1.scatter(*zip(*target_points), c='red', label='Target Points')
        ax1.grid(True)
        ax1.legend()

        # Plot inverse transformed coordinates
        ax2.set_title("Inverse Transformed Coordinates")
        if self.original_image is not None:
            ax2.imshow(self.original_image)
        inverse_transformed_points = self.converter.inverse_convert_points(target_points)
        ax2.scatter(*zip(*inverse_transformed_points), c='blue', label='Inverse Transformed Points')
        if source_points:
            ax2.scatter(*zip(*source_points), c='green', marker='x', label='Expected Points')
        ax2.grid(True)
        ax2.legend()

        # Add connecting lines between corresponding points
        for tgt, inv in zip(target_points, inverse_transformed_points):
            ax1.plot([tgt[0]], [tgt[1]], 'ro')
            ax2.plot([inv[0]], [inv[1]], 'bo')

        plt.suptitle(title)
        plt.tight_layout()
        return fig


def main():
    """
    Example usage of the CoordinateVisualizer.
    """
    # Example points in simulation space
    sim_points = [(0, 0), (700, 0), (0, 700), (700, 700), (350, 350)]

    # Create converter with the same parameters as in message_converter.py
    sim_origin = (0, 0)
    sim_unit_ft = 0.784
    sim_unit_m = sim_unit_ft / 3.281

    frontend_origin_x = 61.1 / sim_unit_ft
    frontend_origin_y = 11.36 / sim_unit_ft
    frontend_origin = (frontend_origin_x, frontend_origin_y)
    frontend_unit_m = 1

    converter = CoordinateConverter(
        source_origin=sim_origin,
        target_origin=frontend_origin,
        rotation_angle=90,
        scale_factor=frontend_unit_m / sim_unit_m,
        reflect_x=False,
        reflect_y=True,
    )

    # Create visualizer with the converter
    visualizer = CoordinateVisualizer(converter=converter, background_image_path=os.path.join(os.path.dirname(__file__), "img", "sim_space.png"))

    # Plot the transformation
    fig = visualizer.plot_coordinate_transformation(
        source_points=sim_points,
        title="Simulation to Frontend Space Transformation"
    )
    fig.savefig(os.path.join(os.path.dirname(__file__), "img", "sim_to_frontend_transformation.png"))

    # Show the plot
    # plt.show()


if __name__ == "__main__":
    main()
