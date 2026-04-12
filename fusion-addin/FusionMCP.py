import adsk.core
import adsk.fusion
import traceback
import json
import time
import threading
from pathlib import Path

app = None
ui = None
stop_thread = False
monitor_thread = None
custom_event = None
custom_event_handler = None

COMM_DIR = Path.home() / "fusion_mcp_comm"
CUSTOM_EVENT_ID = "FusionMCPCommandEvent"

# Thread-safe storage for pending commands: {command_id: command_dict}
_pending_commands = {}
_pending_lock = threading.Lock()


def write_error_response(command_id, error_msg):
    """Write an error response file so the MCP server doesn't hang at the 45s timeout."""
    try:
        resp_file = COMM_DIR / f"response_{command_id}.json"
        with open(resp_file, 'w') as f:
            json.dump({"success": False, "error": str(error_msg)}, f, indent=2)
    except Exception:
        traceback.print_exc()


class CommandEventHandler(adsk.core.CustomEventHandler):
    """Handles command execution on the main thread via CustomEvent dispatch."""
    def __init__(self):
        super().__init__()

    def notify(self, args):
        command_id = None
        try:
            event_args = adsk.core.CustomEventArgs.cast(args)
            command_id = event_args.additionalInfo

            with _pending_lock:
                command = _pending_commands.pop(command_id, None)

            if command is None:
                return

            result = execute_command(command)
            resp_file = COMM_DIR / f"response_{command_id}.json"
            with open(resp_file, 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            traceback.print_exc()
            if command_id:
                write_error_response(command_id, f"Event handler error: {e}")


def run(context):
    global app, ui, monitor_thread, stop_thread, custom_event, custom_event_handler
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        COMM_DIR.mkdir(mode=0o700, exist_ok=True)
        stop_thread = False

        # Register custom event for main-thread dispatch
        custom_event = app.registerCustomEvent(CUSTOM_EVENT_ID)
        custom_event_handler = CommandEventHandler()
        custom_event.add(custom_event_handler)

        monitor_thread = threading.Thread(target=monitor_commands, daemon=True)
        monitor_thread.start()
        ui.messageBox('Fusion MCP Started!\n\nListening at:\n' + str(COMM_DIR))
    except Exception:
        if ui:
            ui.messageBox('Failed:\n' + traceback.format_exc())


def stop(context):
    global stop_thread, ui, custom_event, custom_event_handler, monitor_thread
    try:
        stop_thread = True
        if monitor_thread and monitor_thread.is_alive():
            monitor_thread.join(timeout=0.5)
        if custom_event and custom_event_handler:
            custom_event.remove(custom_event_handler)
        if app:
            app.unregisterCustomEvent(CUSTOM_EVENT_ID)
        if ui:
            ui.messageBox('Fusion MCP Stopped')
    except Exception:
        traceback.print_exc()


def _handle_cmd_error(cmd_file, error_msg):
    """Handle a failed command: write error response and clean up the command file."""
    cmd_id = cmd_file.stem.removeprefix("command_")
    write_error_response(cmd_id, error_msg)
    try:
        cmd_file.unlink()
    except Exception:
        pass


def monitor_commands():
    """Background thread: watches for command files, dispatches to main thread via CustomEvent."""
    global stop_thread
    while not stop_thread:
        try:
            cmd_files = list(COMM_DIR.glob("command_*.json"))
            for cmd_file in cmd_files:
                try:
                    with open(cmd_file, 'r') as f:
                        command = json.load(f)

                    command_id = str(command.get('id', ''))

                    # Stash command for main-thread handler, then fire event
                    with _pending_lock:
                        _pending_commands[command_id] = command

                    app.fireCustomEvent(CUSTOM_EVENT_ID, command_id)

                    # Clean up the command file after dispatching
                    try:
                        cmd_file.unlink()
                    except Exception:
                        pass

                except json.JSONDecodeError as e:
                    _handle_cmd_error(cmd_file, f"Malformed command JSON: {e}")
                except Exception as e:
                    _handle_cmd_error(cmd_file, f"Command processing error: {e}")
            time.sleep(0.1)
        except Exception:
            traceback.print_exc()
            time.sleep(0.1)  # Prevent tight-loop on persistent errors


def execute_command(command):
    global app
    tool_name = command.get('name')
    params = command.get('params', {})
    try:
        design = app.activeProduct
        if not design:
            return {"success": False, "error": "No active design"}
        rootComp = design.rootComponent

        if tool_name == 'create_sketch':
            return create_sketch(design, rootComp, params)
        elif tool_name == 'draw_circle':
            return draw_circle(design, rootComp, params)
        elif tool_name == 'draw_rectangle':
            return draw_rectangle(design, rootComp, params)
        elif tool_name == 'extrude':
            return extrude_profile(design, rootComp, params)
        elif tool_name == 'revolve':
            return revolve_profile(design, rootComp, params)
        elif tool_name == 'fillet':
            return add_fillet(design, rootComp, params)
        elif tool_name == 'finish_sketch':
            return finish_sketch(design, rootComp, params)
        elif tool_name == 'fit_view':
            return fit_view(design, rootComp, params)
        elif tool_name == 'get_design_info':
            return get_design_info(design, rootComp, params)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_sketch(design, rootComp, params):
    plane_name = params.get('plane', 'XY')
    plane_map = {
        'XY': rootComp.xYConstructionPlane,
        'XZ': rootComp.xZConstructionPlane,
        'YZ': rootComp.yZConstructionPlane
    }
    plane = plane_map.get(plane_name)
    sketch = rootComp.sketches.add(plane)
    return {"success": True, "sketch_name": sketch.name}

def draw_circle(design, rootComp, params):
    activeEdit = design.activeEditObject
    if not activeEdit:
        return {"success": False, "error": "No active sketch"}
    sketch = activeEdit
    center = adsk.core.Point3D.create(params['center_x'], params['center_y'], 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, params['radius'])
    return {"success": True}

def draw_rectangle(design, rootComp, params):
    activeEdit = design.activeEditObject
    if not activeEdit:
        return {"success": False, "error": "No active sketch"}
    sketch = activeEdit
    p1 = adsk.core.Point3D.create(params['x1'], params['y1'], 0)
    p2 = adsk.core.Point3D.create(params['x2'], params['y2'], 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)
    return {"success": True}

def extrude_profile(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches"}
    sketch = rootComp.sketches.item(rootComp.sketches.count - 1)
    if sketch.profiles.count == 0:
        return {"success": False, "error": "No profiles"}
    profile = sketch.profiles.item(sketch.profiles.count - 1)
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(params['distance']))
    extrude = extrudes.add(extInput)
    return {"success": True, "feature_name": extrude.name}

def revolve_profile(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches"}
    sketch = rootComp.sketches.item(rootComp.sketches.count - 1)
    if sketch.profiles.count == 0:
        return {"success": False, "error": "No profiles"}
    profile = sketch.profiles.item(sketch.profiles.count - 1)
    axis = rootComp.yConstructionAxis
    revolves = rootComp.features.revolveFeatures
    revInput = revolves.createInput(profile, axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    import math
    revInput.setAngleExtent(False, adsk.core.ValueInput.createByReal(math.radians(params['angle'])))
    revolve = revolves.add(revInput)
    return {"success": True, "feature_name": revolve.name}

def add_fillet(design, rootComp, params):
    if rootComp.bRepBodies.count == 0:
        return {"success": False, "error": "No bodies"}
    body = rootComp.bRepBodies.item(rootComp.bRepBodies.count - 1)
    edges = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        edges.add(edge)
    fillets = rootComp.features.filletFeatures
    filletInput = fillets.createInput()
    filletInput.addConstantRadiusEdgeSet(edges, adsk.core.ValueInput.createByReal(params['radius']), True)
    fillet = fillets.add(filletInput)
    return {"success": True, "feature_name": fillet.name}

def finish_sketch(design, rootComp, params):
    design.activeEditObject = None
    return {"success": True, "message": "Sketch finished"}

def fit_view(design, rootComp, params):
    global app
    app.activeViewport.fit()
    return {"success": True}

def get_design_info(design, rootComp, params):
    return {
        "success": True,
        "design_name": design.parentDocument.name,
        "body_count": rootComp.bRepBodies.count,
        "sketch_count": rootComp.sketches.count
    }
