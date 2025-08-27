import bpy
import time
import threading

def run_photogrammetry_process(context, settings):
    
    wm = context.window_manager
    
    try:
        wm.photogrammetry_progress = 'Step 1/4: Extracting frames...'
        print("Extracting frames...")
        time.sleep(2) # Placeholder for actual work

        wm.photogrammetry_progress = 'Step 2/4: Running COLMAP...'
        print("Running COLMAP...")
        time.sleep(2) # Placeholder for actual work

        wm.photogrammetry_progress = 'Step 3/4: Importing data...'
        print("Importing data...")
        time.sleep(2) # Placeholder for actual work
        
        wm.photogrammetry_progress = 'Step 4/4: Cleaning up...'
        print("Cleaning up...")
        time.sleep(2) # Placeholder for actual work

        # The monitor will set the final "Finished!" message.
        
    except Exception as e:
        wm.photogrammetry_progress = f"Error: {e}"

class OT_start_photogrammetry(bpy.types.Operator):
    bl_idname = "oneshot.generate_scene"
    bl_label = "Generate 3D Scene"
    
    _thread = None

    def execute(self, context):
        settings = context.scene.photogrammetry_settings
        context.window_manager.photogrammetry_progress = 'Starting...'
        
        OT_start_photogrammetry._thread = threading.Thread(target=run_photogrammetry_process, args=(context, settings))
        OT_start_photogrammetry._thread.start()
        
        bpy.ops.wm.photogrammetry_monitor('INVOKE_DEFAULT')
        return {'FINISHED'}

class OT_photogrammetry_monitor(bpy.types.Operator):
    bl_idname = "wm.photogrammetry_monitor"
    bl_label = "Photogrammetry Monitor"
    
    _timer = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            if OT_start_photogrammetry._thread and OT_start_photogrammetry._thread.is_alive():
                # Redraw the view so the progress text updates
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                return {'PASS_THROUGH'}
            else:
                self.cancel(context)
                context.window_manager.photogrammetry_progress = 'Finished!'
                # Redraw the view a final time
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                return {'FINISHED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)

class OneShot_OT_Import(bpy.types.Operator):
    bl_idname = "oneshot.import_operator"
    bl_label = "oneShot Import"

    def execute(self, context):
        print("Importing...")
        return {'FINISHED'}

class OneShot_OT_Export(bpy.types.Operator):
    bl_idname = "oneshot.export_operator"
    bl_label = "oneShot Export"

    def execute(self, context):
        print("Exporting...")
        return {'FINISHED'}

classes = (
    OT_start_photogrammetry,
    OT_photogrammetry_monitor,
    OneShot_OT_Import,
    OneShot_OT_Export,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
