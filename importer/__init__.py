import os
import traceback
from .file_handlers.colmap_file_handler import ColmapFileHandler
from .importers.camera_importer import CameraImporter
from .importers.point_importer import PointImporter
from .importers.mesh_importer import MeshImporter
from .blender_utility.object_utility import add_collection
from .blender_utility.logging_utility import log_report
from .types.camera import Camera

# Assuming GeneralOptions is not found and thus omitted from inheritance
# If GeneralOptions is meant to be a mixin for settings, its properties will be copied by the __init__ method.

class ColmapImportController(CameraImporter, PointImporter, MeshImporter):
    """
    A controller to manage the COLMAP import process, inheriting import functionalities
    and handling UI settings.
    """
    def __init__(self, settings):
        """
        Initialize the controller with import settings from the UI.
        All properties from the settings object are dynamically copied to this instance.
        Properties are first initialized with default values from PhotogrammetrySettings
        and importer base classes to prevent AttributeError. Explicit mapping is used
        for properties with differing names between UI settings and importer.
        """
        # Initialize all properties with default values from PhotogrammetrySettings and importer base classes
        # StringProperty
        self.input_path = ""
        self.output_path = ""
        self.colmap_model_path = ""
        self.image_dp = ""
        self.depth_map_id_or_name_str = "" # From CameraImporter
        self.default_focal_length = float("nan") # From CameraImporter
        self.default_pp_x = float("nan") # From CameraImporter
        self.default_pp_y = float("nan") # From CameraImporter

        # BoolProperty
        self.use_workspace_images = True
        self.import_cameras = True
        self.add_background_image_for_each_camera = True # From PhotogrammetrySettings
        self.add_background_images = True # Mapped for CameraImporter
        self.add_image_plane_for_each_camera = False # From PhotogrammetrySettings
        self.add_image_planes = False # Mapped for CameraImporter
        self.add_image_plane_emission = True # From CameraImporter
        self.add_depth_maps = False # From PhotogrammetrySettings
        self.add_depth_maps_as_point_cloud = False # Mapped for CameraImporter
        self.use_default_depth_map_color = False # From CameraImporter
        self.add_camera_motion_as_animation = True
        self.add_background_images_for_animated_camera = True # From PhotogrammetrySettings
        self.add_animated_camera_background_images = True # Mapped for CameraImporter
        self.reorganize_undistorted_images = True # From CameraImporter
        self.adjust_frame_numbers_of_camera_animation = True # From PhotogrammetrySettings
        self.consider_missing_cameras_during_animation = True # Mapped for CameraImporter
        self.remove_rotation_discontinuities = True
        self.suppress_distortion_warnings = True
        self.adjust_render_settings = True
        self.import_points = True
        self.center_data_around_origin = False # From PhotogrammetrySettings
        self.center_points = False # From PointImporter
        self.draw_points_in_3d_view_with_opengl = True # From PhotogrammetrySettings
        self.draw_points_with_gpu = True # Mapped for PointImporter
        self.add_point_data_to_point_cloud_handle = True # From PhotogrammetrySettings
        self.add_points_to_point_cloud_handle = True # Mapped for PointImporter
        self.add_points_as_mesh_object = False # From PhotogrammetrySettings
        self.add_points_as_mesh_oject = False # Mapped for PointImporter (typo in original)
        self.add_mesh_to_point_geometry_nodes = True # From PointImporter
        self.add_color_as_custom_property = True # From PointImporter
        self.import_mesh = False # From PhotogrammetrySettings
        self.add_mesh_color_emission = True # From MeshImporter
        self.adjust_clipping_distance = False # From PhotogrammetrySettings

        # FloatProperty
        self.initial_camera_extent = 1.0 # From PhotogrammetrySettings
        self.camera_extent = 1.0 # Mapped for CameraImporter
        self.image_plane_transparency = 0.5 # From CameraImporter
        self.depth_map_default_color = (0.0, 1.0, 0.0) # From CameraImporter
        self.point_radius = 0.05 # From PointImporter

        # EnumProperty
        self.interpolation_type = 'LINEAR' # Default from EnumProperty items
        self.animation_frame_source = 'ORIGINAL' # From CameraImporter
        self.image_fp_type = Camera.IMAGE_FP_TYPE_NAME # From CameraImporter

        # IntProperty
        self.point_cloud_display_sparsity = 1 # From PhotogrammetrySettings
        self.initial_point_size = 5 # From PhotogrammetrySettings
        self.point_size = 5 # Mapped for PointImporter
        self.depth_map_display_sparsity = 10 # From CameraImporter
        self.number_interpolation_frames = 0 # From CameraImporter
        self.default_width = -1 # From CameraImporter
        self.default_height = -1 # From CameraImporter
        self.point_subdivisions = 1 # From PointImporter

        # Now, dynamically copy values from the provided settings object,
        # overwriting defaults if the property exists in settings.
        # This loop will handle properties with matching names and re-mappings.
        for prop_name in dir(settings):
            if not prop_name.startswith('__') and not prop_name.startswith('bl_'):
                try:
                    if hasattr(settings, prop_name) and not callable(getattr(settings, prop_name)):
                        # Handle specific re-mappings
                        if prop_name == 'add_background_image_for_each_camera':
                            self.add_background_images = settings.add_background_image_for_each_camera
                        elif prop_name == 'add_image_plane_for_each_camera':
                            self.add_image_planes = settings.add_image_plane_for_each_camera
                        elif prop_name == 'add_depth_maps':
                            self.add_depth_maps_as_point_cloud = settings.add_depth_maps
                        elif prop_name == 'add_background_images_for_animated_camera':
                            self.add_animated_camera_background_images = settings.add_background_images_for_animated_camera
                        elif prop_name == 'adjust_frame_numbers_of_camera_animation':
                            self.consider_missing_cameras_during_animation = settings.adjust_frame_numbers_of_camera_animation
                        elif prop_name == 'initial_camera_extent':
                            self.camera_extent = settings.initial_camera_extent
                        elif prop_name == 'center_data_around_origin':
                            self.center_points = settings.center_data_around_origin
                        elif prop_name == 'draw_points_in_3d_view_with_opengl':
                            self.draw_points_with_gpu = settings.draw_points_in_3d_view_with_opengl
                        elif prop_name == 'add_point_data_to_point_cloud_handle':
                            self.add_points_to_point_cloud_handle = settings.add_point_data_to_point_cloud_handle
                        elif prop_name == 'initial_point_size':
                            self.point_size = settings.initial_point_size
                        elif prop_name == 'add_points_as_mesh_object':
                            self.add_points_as_mesh_oject = settings.add_points_as_mesh_object
                        else:
                            # For all other matching names, copy directly
                            setattr(self, prop_name, getattr(settings, prop_name))
                except AttributeError:
                    pass
        
    def report(self, report_type, msg):
        """Log a report message using the addon's logging utility."""
        log_report(str(report_type), str(msg))


def import_colmap_scene(reconstruction_folder_path, settings):
    """
    Imports a COLMAP scene into Blender based on the provided reconstruction folder
    and UI settings.

    This function orchestrates the parsing of COLMAP files and the subsequent
    import of cameras, points, and meshes into a new Blender collection.
    """
    controller = ColmapImportController(settings)

    log_report("INFO", f"Starting COLMAP scene import from: {reconstruction_folder_path}")

    try:
        # Parse COLMAP files.
        # Note: ColmapFileHandler.read_colmap_model does not exist.
        # Using ColmapFileHandler.parse_colmap_folder as it is the most comprehensive
        # existing function for parsing COLMAP data (handles both model and workspace
        # folders and returns mesh information).
        cameras, points, mesh_ifp = ColmapFileHandler.parse_colmap_folder(
            idp=reconstruction_folder_path,
            use_workspace_images=getattr(controller, 'use_workspace_images', False), # Use getattr with default for robustness
            image_dp=getattr(controller, 'image_dp', ''),
            image_fp_type=Camera.IMAGE_FP_TYPE_NAME,
            suppress_distortion_warnings=getattr(controller, 'suppress_distortion_warnings', False),
            op=controller,
        )

        reconstruction_collection = add_collection("Reconstruction Collection")

        # Call import methods on the controller instance, conditioned by settings
        if getattr(controller, 'import_cameras', False):
            controller.import_photogrammetry_cameras(cameras, reconstruction_collection)
        if getattr(controller, 'import_points', False):
            controller.import_photogrammetry_points(points, reconstruction_collection)
        if getattr(controller, 'import_mesh', False) and mesh_ifp:
            controller.import_photogrammetry_mesh(mesh_ifp, reconstruction_collection)

        log_report("INFO", "COLMAP scene imported successfully.")
        return True

    except Exception as e:
        log_report("ERROR", f"Error during COLMAP import: {e}")
        traceback.print_exc()
        return False
