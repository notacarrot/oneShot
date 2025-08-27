import bpy
import threading
import time

def run_photogrammetry_process(context):
    wm = context.window_manager
    wm.oneshot_progress = "Step 1/3: Preparing..."
    time.sleep(2)
    wm.oneshot_progress = "Step 2/3: Processing..."
    time.sleep(2)
    wm.oneshot_progress = "Step 3/3: Finalizing..."
    time.sleep(2)
    wm.oneshot_progress = "Finished!"

class ONESHOT_OT_start_photogrammetry(bpy.types.Operator):
    bl_idname = "oneshot.start_photogrammetry"
    bl_label = "Start Photogrammetry"
    bl_description = "Starts the photogrammetry process"

    def execute(self, context):
        wm = context.window_manager
        wm.oneshot_progress = "Starting process..."

        # Create and start a new thread for the long-running process
        thread = threading.Thread(target=run_photogrammetry_process, args=(context,))
        thread.start()

        # Store the thread in the window manager for the modal operator to monitor
        wm.oneshot_photogrammetry_thread = thread

        # Invoke the modal operator to monitor the thread
        return context.window_manager.invoke_props_dialog(self, width=400)

    def invoke(self, context, event):
        # This invoke is for the dialog, the actual modal operator is invoked below
        return context.window_manager.invoke_modal(ONESHOT_OT_monitor_photogrammetry.bl_idname)

class ONESHOT_OT_monitor_photogrammetry(bpy.types.Operator):
    bl_idname = "oneshot.monitor_photogrammetry"
    bl_label = "Monitor Photogrammetry"

    _timer = None
    _thread = None

    def invoke(self, context, event):
        wm = context.window_manager
        self._thread = wm.oneshot_photogrammetry_thread

        if not self._thread or not self._thread.is_alive():
            self.report({'INFO'}, "Photogrammetry process not running.")
            return {'FINISHED'}

        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            if not self._thread.is_alive():
                self.report({'INFO'}, "Photogrammetry process finished.")
                context.window_manager.event_timer_remove(self._timer)
                del context.window_manager.oneshot_photogrammetry_thread
                return {'FINISHED'}
            else:
                # Force UI redraw to update progress text
                context.area.tag_redraw()
        return {'PASS_THROUGH'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        self.report({'INFO'}, "Photogrammetry monitoring cancelled.")
        if hasattr(context.window_manager, 'oneshot_photogrammetry_thread'):
            del context.window_manager.oneshot_photogrammetry_thread
