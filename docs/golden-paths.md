# Golden Path Workflows

Three reference workflows that demonstrate correct usage of the Fusion 360 MCP tools. Each workflow covers a common CAD task from start to finish, including verification steps.

All dimensions are in **centimeters** (ADR-D003).

---

## GP1: Extruded Box (Beginner)

**Goal**: Create a simple 5cm x 3cm x 2cm box with 0.3cm fillets.

### Steps

1. **Verify connectivity**
   ```
   ping()
   ```
   Expected: `{success: true, ...}` within 5 seconds.

2. **Create base sketch**
   ```
   create_sketch(plane="XY")
   draw_rectangle(length=5.0, width=3.0, center_x=0.0, center_y=0.0)
   ```

3. **Extrude to height**
   ```
   extrude(distance=2.0, direction="positive")
   ```

4. **Add fillets**
   ```
   fillet(radius=0.3)
   ```

5. **Verify dimensions**
   ```
   measure(measurement_type="body")
   ```
   Expected: bounding box approximately 5.0 x 3.0 x 2.0 cm.

6. **Export**
   ```
   export_stl(filepath="~/Desktop/box.stl")
   ```

---

## GP2: Revolved Body with Z-Negation (Intermediate)

**Goal**: Create a revolved vase profile on the XZ plane, demonstrating Z-axis negation (ADR-D004).

### Steps

1. **Verify connectivity**
   ```
   ping()
   ```

2. **Create sketch on XZ plane**
   ```
   create_sketch(plane="XZ")
   ```
   **Critical**: When sketching on XZ plane, the sketch Y-axis maps to World Z, and World Z values are **negated** in sketch coordinates.

3. **Draw vase profile**
   Draw a closed profile using lines and arcs. Remember:
   - Sketch X = World X
   - Sketch Y = -World Z (negated!)
   - To place geometry at World Z=5cm, use sketch Y=-5.0

   ```
   draw_line(x1=0, y1=0, x2=2, y2=0)
   draw_arc(center_x=2, center_y=-2.5, start_x=2, start_y=0, end_x=4.5, end_y=-2.5)
   draw_line(x1=4.5, y1=-2.5, x2=4.5, y2=-8)
   draw_line(x1=4.5, y1=-8, x2=0, y2=-8)
   draw_line(x1=0, y1=-8, x2=0, y2=0)
   ```

4. **Revolve around axis**
   ```
   revolve(axis="Z", angle=360)
   ```

5. **Verify**
   ```
   measure(measurement_type="body")
   ```

---

## GP3: Two-Component Assembly (Advanced)

**Goal**: Create a box and a lid as separate components, then position them.

### Steps

1. **Verify connectivity**
   ```
   ping()
   ```

2. **Create box component**
   ```
   create_component(name="Box")
   create_sketch(plane="XY")
   draw_rectangle(length=6.0, width=4.0, center_x=0.0, center_y=0.0)
   extrude(distance=3.0)
   shell(thickness=0.3, open_face="top")
   ```

3. **Create lid component**
   ```
   create_component(name="Lid")
   create_sketch(plane="XY")
   draw_rectangle(length=6.2, width=4.2, center_x=0.0, center_y=0.0)
   extrude(distance=0.5)
   ```

4. **Position lid on top of box**
   ```
   move_component(component_name="Lid", dx=0.0, dy=0.0, dz=3.0)
   ```
   The lid is moved up by the box height (3cm).

5. **Verify assembly**
   ```
   get_design_info()
   ```
   Expected: 2 components ("Box", "Lid"), each with 1 body.

6. **Export assembly**
   ```
   export_step(filepath="~/Desktop/box_assembly.step")
   ```

---

## Verification Checklist

After completing any workflow:

- [ ] `ping()` succeeds (connectivity)
- [ ] `get_design_info()` shows expected component/body count
- [ ] `measure()` returns dimensions within tolerance of design intent
- [ ] Export produces a valid file in the target directory
