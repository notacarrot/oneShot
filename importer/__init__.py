import bpy
import os
import numpy as np

# Relative imports from the photogrammetry_importer package
from .file_handlers.colmap_file_handler import ColmapFileHandler
from .importers.camera_importer import CameraImporter
from .importers.point_importer import PointImporter
from .importers.mesh_importer import MeshImporter
from .blender_utility.object_utility import add_collection
from .blender_utility.logging_utility import log_report
from .types.camera import Camera # Needed for Camera.IMAGE_FP_TYPE_NAME

# Dummy class to hold properties similar to an operator for the importer functions
# This is a simplified version, only including properties used by the importers
class DummyImporterProperties:
    def __init__(self):
        self.use_workspace_images = False
        self.image_fp_type = Camera.IMAGE_FP_TYPE_NAME
        self.image_dp = ""
        self.suppress_distortion_warnings = False
        self.import_cameras = True
        self.add_background_images = True
        self.add_image_planes = False
        self.import_points = True
        self.add_points_as_mesh_oject = True
        self.add_mesh_to_point_geometry_nodes = True
        self.import_mesh = False # Default to False as per request
        self.add_mesh_color_emission = True
        # Add other properties with default values if they are used by the importer functions
        # For camera_importer.py
        self.default_width = -1
        self.default_height = -1
        self.default_focal_length = float("nan")
        self.default_pp_x = float("nan")
        self.default_pp_y = float("nan")
        self.add_depth_maps_as_point_cloud = False
        self.use_default_depth_map_color = False
        self.depth_map_default_color = (0.0, 1.0, 0.0)
        self.depth_map_display_sparsity = 10
        self.depth_map_id_or_name_str = ""
        self.add_camera_motion_as_animation = False # Not requested, default to False
        self.animation_frame_source = "ORIGINAL"
        self.add_animated_camera_background_images = True
        self.reorganize_undistorted_images = True
        self.number_interpolation_frames = 0
        self.interpolation_type = "LINEAR"
        self.consider_missing_cameras_during_animation = True
        self.remove_rotation_discontinuities = True
        self.adjust_render_settings = True
        self.camera_extent = 1

        # For point_importer.py
        self.point_cloud_display_sparsity = 1
        self.center_points = False
        self.draw_points_with_gpu = True
        self.add_points_to_point_cloud_handle = True
        self.point_size = 5
        # self.add_points_as_mesh_oject = True # Overwritten by the one above
        # self.add_mesh_to_point_geometry_nodes = True # Overwritten by the one above
        self.point_radius = 0.05
        self.point_subdivisions = 1
        self.add_color_as_custom_property = True

        # For mesh_importer.py
        # self.import_mesh = False # Overwritten by the one above
        # self.add_mesh_color_emission = True # Overwritten by the one above


def import_colmap_scene(reconstruction_dir_path: str) -> bool:
    log_report("INFO", f"oneShot: Importing COLMAP scene from: {reconstruction_dir_path}")

    # Create a dummy object to mimic the operator's properties
    importer_props = DummyImporterProperties()

    # Instantiate the importers
    camera_importer = CameraImporter()
    point_importer = PointImporter()
    mesh_importer = MeshImporter()

    # Manually set the properties of the importer instances from the dummy object
    # This is necessary because the importer methods expect these properties to be present on 'self'
    for prop_name in dir(importer_props):
        if not prop_name.startswith('__'):
            if hasattr(camera_importer, prop_name):
                setattr(camera_importer, prop_name, getattr(importer_props, prop_name))
            if hasattr(point_importer, prop_name):
                setattr(point_importer, prop_name, getattr(importer_props, prop_name))
            if hasattr(mesh_importer, prop_name):
                setattr(mesh_importer, prop_name, getattr(importer_props, prop_name))

    try:
        # Parse COLMAP data
        # The parse_colmap_folder expects an 'op' argument for logging, we pass None
        cameras, points, mesh_ifp = ColmapFileHandler.parse_colmap_folder(
            idp=reconstruction_dir_path,
            use_workspace_images=importer_props.use_workspace_images,
            image_dp=importer_props.image_dp,
            image_fp_type=importer_props.image_fp_type,
            suppress_distortion_warnings=importer_props.suppress_distortion_warnings,
            op=None, # No operator instance available
        )
        log_report("INFO", f"oneShot: Number cameras: {len(cameras)}")
        log_report("INFO", f"oneShot: Number points: {len(points)}")
        log_report("INFO", f"oneShot: Mesh file path: {mesh_ifp}")

        reconstruction_collection = add_collection("Reconstruction Collection")

        # Import cameras
        camera_importer.import_photogrammetry_cameras(cameras, reconstruction_collection)

        # Import points
        point_importer.import_photogrammetry_points(points, reconstruction_collection)

        # Import mesh (if available and requested)
        if importer_props.import_mesh and mesh_ifp:
            mesh_importer.import_photogrammetry_mesh(mesh_ifp, reconstruction_collection)
        else:
            log_report("INFO", "oneShot: Mesh import skipped (not requested or not available).")

        # apply_general_options is part of ImportOperator and GeneralOptions,
        # which are base classes for the original operator.
        # Since we are not using the operator, we need to manually apply any general options
        # that are critical. For now, we'll skip this as the request doesn't specify
        # any general options to apply. If coordinate system transformation is needed,
        # it would go here.

        log_report("INFO", "oneShot: COLMAP scene import finished successfully.")
        return True

    except Exception as e:
        log_report("ERROR", f"oneShot: Error importing COLMAP scene: {e}")
        return False
