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
        """
        # Call __init__ for all base classes if they have one.
        # Since CameraImporter, PointImporter, MeshImporter are likely mixins without
        # complex __init__ methods, a simple super().__init__() might not be appropriate
        # or necessary if they don't define one.
        # The previous code did not call super().__init__(), so I will follow that convention.
        
        for prop_name in dir(settings):
            # Avoid copying built-in attributes and Blender-specific internal properties
            if not prop_name.startswith('__') and not prop_name.startswith('bl_'):
                try:
                    setattr(self, prop_name, getattr(settings, prop_name))
                except AttributeError:
                    # Some properties might not be directly readable or settable, skip them
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
