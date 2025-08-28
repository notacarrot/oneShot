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

def import_colmap_scene(
    reconstruction_dir_path: str,
    import_cameras=True,
    add_background_image=True,
    add_camera_motion=True,
    import_points=True,
    add_points_as_mesh_object=False,
) -> bool:
    log_report("INFO", f"oneShot: Importing COLMAP scene from: {reconstruction_dir_path}")

    # Create a dummy object to mimic the operator's properties
    class DummyImporterProperties:
        def __init__(self):
            self.use_workspace_images = False
            self.image_fp_type = Camera.IMAGE_FP_TYPE_NAME
            self.image_dp = ""
            self.suppress_distortion_warnings = True
            self.import_cameras = import_cameras
            self.add_background_images = add_background_image
            self.add_image_planes = False
            self.import_points = import_points
            self.add_points_as_mesh_oject = add_points_as_mesh_object
            self.add_mesh_to_point_geometry_nodes = True
            self.import_mesh = False
            self.add_mesh_color_emission = True
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
            self.add_camera_motion_as_animation = add_camera_motion
            self.animation_frame_source = "ORIGINAL"
            self.add_animated_camera_background_images = True
            self.reorganize_undistorted_images = True
            self.number_interpolation_frames = 0
            self.interpolation_type = "LINEAR"
            self.consider_missing_cameras_during_animation = True
            self.remove_rotation_discontinuities = True
            self.adjust_render_settings = True
            self.camera_extent = 1
            self.point_cloud_display_sparsity = 1
            self.center_points = False
            self.draw_points_with_gpu = True
            self.add_points_to_point_cloud_handle = True
            self.point_size = 5
            self.point_radius = 0.05
            self.point_subdivisions = 1
            self.add_color_as_custom_property = True

    importer_props = DummyImporterProperties()

    camera_importer = CameraImporter()
    point_importer = PointImporter()
    mesh_importer = MeshImporter()

    for prop_name in dir(importer_props):
        if not prop_name.startswith('__'):
            if hasattr(camera_importer, prop_name):
                setattr(camera_importer, prop_name, getattr(importer_props, prop_name))
            if hasattr(point_importer, prop_name):
                setattr(point_importer, prop_name, getattr(importer_props, prop_name))
            if hasattr(mesh_importer, prop_name):
                setattr(mesh_importer, prop_name, getattr(importer_props, prop_name))

    try:
        cameras, points, mesh_ifp = ColmapFileHandler.parse_colmap_folder(
            idp=reconstruction_dir_path,
            use_workspace_images=importer_props.use_workspace_images,
            image_dp=importer_props.image_dp,
            image_fp_type=importer_props.image_fp_type,
            suppress_distortion_warnings=importer_props.suppress_distortion_warnings,
            op=None,
        )

        reconstruction_collection = add_collection("Reconstruction Collection")

        if importer_props.import_cameras:
            camera_importer.import_photogrammetry_cameras(cameras, reconstruction_collection)

        if importer_props.import_points:
            point_importer.import_photogrammetry_points(points, reconstruction_collection)

        if importer_props.import_mesh and mesh_ifp:
            mesh_importer.import_photogrammetry_mesh(mesh_ifp, reconstruction_collection)

        log_report("INFO", "oneShot: COLMAP scene import finished successfully.")
        return True

    except Exception as e:
        log_report("ERROR", f"oneShot: Error importing COLMAP scene: {e}")
        return False
