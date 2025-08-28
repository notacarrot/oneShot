import os
import traceback
from .file_handlers.colmap_file_handler import ColmapFileHandler
from .importers.camera_importer import CameraImporter
from .importers.point_importer import PointImporter
from .importers.mesh_importer import MeshImporter
from .blender_utility.object_utility import add_collection
from .blender_utility.logging_utility import log_report
from .types.camera import Camera


class ColmapImportController(CameraImporter, PointImporter, MeshImporter):
    """A controller to manage the COLMAP import process."""

    def __init__(self, settings):
        """Initialize the controller with import settings."""
        for prop in dir(settings):
            if not prop.startswith("__") and not prop.startswith("bl_"):
                setattr(self, prop, getattr(settings, prop))

    def report(self, report_type, msg):
        """Log a report message."""
        log_report(str(report_type), str(msg))


def import_colmap_scene(reconstruction_folder_path, settings):
    """
    Import a COLMAP scene, including cameras, points, and mesh.

    This function parses the COLMAP files, creates a controller with the
    given settings, and then imports the scene components into Blender.
    """
    controller = ColmapImportController(settings)

    log_report(
        "INFO", f"Starting COLMAP scene import from: {reconstruction_folder_path}"
    )

    try:
        cameras, points, mesh_ifp = ColmapFileHandler.parse_colmap_folder(
            idp=reconstruction_folder_path,
            use_workspace_images=controller.use_workspace_images,
            image_dp=controller.image_dp,
            image_fp_type=Camera.IMAGE_FP_TYPE_NAME,
            suppress_distortion_warnings=controller.suppress_distortion_warnings,
            op=controller,
        )

        reconstruction_collection = add_collection("Reconstruction Collection")

        if controller.import_cameras:
            controller.import_photogrammetry_cameras(
                cameras, reconstruction_collection
            )
        if controller.import_points:
            controller.import_photogrammetry_points(
                points, reconstruction_collection
            )
        if controller.import_mesh and mesh_ifp:
            controller.import_photogrammetry_mesh(
                mesh_ifp, reconstruction_collection
            )

        log_report("INFO", "COLMAP scene imported successfully.")
        return True

    except Exception as e:
        log_report("ERROR", f"Error during COLMAP import: {e}")
        traceback.print_exc()
        return False
