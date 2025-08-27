import bpy


def get_selected_object():
    """Get the selected object or return None."""
    selection_names = [obj.name for obj in bpy.context.selected_objects]
    if len(selection_names) == 0:
        return None
    selected_obj = bpy.data.objects[selection_names[0]]
    return selected_obj


def get_selected_empty():
    """Get the selected empty or return None."""
    selected_obj = get_selected_object()
    if selected_obj is None:
        return None
    elif selected_obj.type == "EMPTY":
        return selected_obj
    else:
        return None


def get_selected_camera():
    """Get the selected camera or return None."""
    selected_obj = get_selected_object()
    if selected_obj is None:
        return None
    elif selected_obj.type == "CAMERA":
        return selected_obj
    else:
        return None


def get_scene_animation_indices():
    """Get the animation indices of the scene."""
    scene = bpy.context.scene
    return range(scene.frame_start, scene.frame_end)


def get_object_animation_indices(obj):
    """Get the animation indices of the object."""
    animation_data = obj.animation_data
    fcurves = animation_data.action.fcurves
    fcu = fcurves[0]
    kp_indices = [int(kp.co[0]) for kp in fcu.keyframe_points]
    return kp_indices

import platform
import requests

def get_colmap_url():
    """
    Get the download URL for the latest COLMAP release for the current OS.

    Returns:
        str: The download URL for the latest COLMAP release.
    """
    os_name = platform.system()
    if os_name == "Windows":
        asset_name = "COLMAP--windows-cuda.zip"
    elif os_name == "Linux":
        asset_name = "COLMAP--linux-cuda.zip"
    else:
        raise Exception(f"Unsupported OS: {os_name}")

    url = "https://api.github.com/repos/colmap/colmap/releases/latest"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    for asset in data["assets"]:
        if asset["name"].endswith(asset_name):
            return asset["browser_download_url"]

    raise Exception(f"Could not find asset for {os_name}")