# Fusion 360 MCP Server

Control Autodesk Fusion 360 with Claude AI through the Model Context Protocol (MCP).

![MCP Version](https://img.shields.io/badge/MCP-1.0-blue)
![Fusion 360](https://img.shields.io/badge/Fusion%20360-2024+-orange)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## What This Does

![Fusion 360 MCP Demo](images/hero-demo.gif)
*Ask Claude to create a part, watch it appear in Fusion 360*

This MCP server lets Claude AI directly control Fusion 360 to:
- Create 3D sketches, extrusions, and revolves
- Build multi-component assemblies with proper positioning
- Apply fillets, chamfers, shells, and patterns
- Export to STL, STEP, and 3MF formats
- Measure geometry and verify designs

**Example prompt:** *"Create a 50mm cube with 5mm rounded edges"* â†’ Claude creates it directly in Fusion 360.

---

## Quick Start (5 minutes)

### Prerequisites
- Autodesk Fusion 360 (free for personal use)
- Claude Desktop app with MCP support
- Python 3.10+ with `pip`

### Step 1: Install the MCP Server

```bash
# Install the MCP framework
pip install mcp

# Clone this repository (or download ZIP)
git clone https://github.com/markwoitaszek/ClaudeFusion360MCP.git
cd ClaudeFusion360MCP
```

### Step 2: Install the Fusion 360 Add-in

1. Open Fusion 360
2. Go to **Utilities** â†’ **ADD-INS** (or press `Shift+S`)
3. Click **Add-Ins** tab â†’ **Green Plus (+)** button
4. Navigate to the `fusion-addin` folder from this repo
5. Select `FusionMCP` folder â†’ Click **Open**
6. Check **Run on Startup** â†’ Click **Run**

You should see: *"Fusion MCP Started! Listening at: C:\Users\...\fusion_mcp_comm"*

![Add-in Success](images/addon-success.png)
*Successfully installed FusionMCP add-in*

### Step 3: Configure Claude Desktop

Edit your Claude Desktop config file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this to the `mcpServers` section:

```json
{
  "mcpServers": {
    "fusion360": {
      "command": "python",
      "args": ["C:/path/to/fusion360-mcp/mcp-server/fusion360_mcp_server.py"]
    }
  }
}
```

> **Note:** Use forward slashes in the path, even on Windows.

### Step 4: Add the Skill File (Recommended)

For best results, create a **Claude Project** and paste the contents of `docs/SKILL.md` into the **Project Instructions**. This teaches Claude:
- Fusion 360 coordinate system rules
- Unit conventions (everything in centimeters!)
- Best practices for assemblies
- Common pitfalls to avoid

**For advanced spatial reasoning**, also include `docs/SPATIAL_AWARENESS.md`. This teaches Claude:
- How to verify geometry placement BEFORE operations
- Coordinate mapping between sketch planes and world space
- The critical Z-negation rule for XZ/YZ planes
- Pre/post operation verification protocols

### Step 5: Restart and Test

1. Restart Claude Desktop
2. Open Fusion 360 (ensure the add-in is running)
3. Ask Claude: *"Create a simple box that is 5cm x 3cm x 2cm"*

---

## How It Works

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     MCP      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    File     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Claude    â”‚ â†â†’ Protocol â†’ â”‚  MCP Server         â”‚ â†â†’ System â†â†’ â”‚  Fusion 360 â”‚
â”‚   Desktop   â”‚              â”‚  (fusion360_mcp_    â”‚             â”‚  Add-in     â”‚
â”‚             â”‚              â”‚   server.py)        â”‚             â”‚  (FusionMCP)â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜             â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

1. Claude sends commands via MCP protocol
2. MCP server writes command to `~/fusion_mcp_comm/command_*.json`
3. Fusion add-in polls for commands, executes them via Fusion API
4. Results written to `~/fusion_mcp_comm/response_*.json`
5. MCP server returns result to Claude

---

## Available Tools

| Category | Tools |
|----------|-------|
| **Sketching** | `create_sketch`, `draw_rectangle`, `draw_circle`, `draw_line`, `draw_arc`, `draw_polygon`, `finish_sketch`, `batch` |
| **3D Operations** | `extrude`, `revolve`, `shell`, `draft` |
| **Modifications** | `fillet`, `chamfer`, `combine` |
| **Patterns** | `pattern_rectangular`, `pattern_circular`, `mirror` |
| **Components** | `create_component`, `move_component`, `rotate_component`, `list_components`, `delete_component`, `check_interference` |
| **Joints** | `create_revolute_joint`, `create_slider_joint`, `set_joint_angle`, `set_joint_distance` |
| **Export/Import** | `export_stl`, `export_step`, `export_3mf`, `import_mesh` |
| **Inspection** | `get_design_info`, `get_body_info`, `measure`, `fit_view` |
| **Utilities** | `undo`, `delete_body`, `delete_sketch` |

See `docs/TOOL_REFERENCE.md` for complete API documentation.

---

## Important: Units Are in Centimeters!

âš ï¸ **All dimensions in the MCP are in CENTIMETERS**, not millimeters.

| You Want | You Enter |
|----------|-----------|
| 50 mm | `5.0` |
| 100 mm | `10.0` |
| 1 inch | `2.54` |

This is the most common source of errors. A value of `50` means 50 cm (half a meter)!

---

## Project Structure

```
fusion360-mcp/
â”œâ”€â”€ README.md                 # This file
â”œâ”€â”€ LICENSE                   # MIT License
â”œâ”€â”€ mcp-server/
â”‚   â””â”€â”€ fusion360_mcp_server.py   # MCP server (run by Claude Desktop)
â”œâ”€â”€ fusion-addin/
â”‚   â”œâ”€â”€ FusionMCP.py          # Fusion 360 add-in code
â”‚   â””â”€â”€ FusionMCP.manifest    # Add-in manifest
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ SKILL.md              # Claude Project instructions
â”‚   â”œâ”€â”€ SPATIAL_AWARENESS.md  # 3D coordinate system & verification
â”‚   â”œâ”€â”€ TOOL_REFERENCE.md     # Complete API reference
â”‚   â””â”€â”€ KNOWN_ISSUES.md       # Common pitfalls and solutions
â””â”€â”€ examples/
    â””â”€â”€ getting_started.md    # Tutorial examples
```
---

## Example Workflows

### Creating a Simple Part
![Simple Box Creation](images/simple-box.png)
*"Create a 5cm cube with 2mm rounded edges"*

### Complex Assembly
![Assembly Example](images/assembly-example.png)
*Multi-component assembly with proper positioning*

### Export Ready Files
![Export Formats](images/export-formats.png)
*Direct export to STL, STEP, and 3MF formats*

---

## Troubleshooting

### "Timeout after 45s" Error
- Fusion 360 is not running, OR
- The FusionMCP add-in is not started
- **Fix:** Open Fusion 360 â†’ Utilities â†’ Add-Ins â†’ Run FusionMCP

### Claude doesn't see the Fusion 360 tools
- MCP server path is wrong in config
- Python can't find the `mcp` package
- **Fix:** Verify path uses forward slashes, run `pip install mcp`

### Dimensions are way too big/small
- You're using millimeters instead of centimeters
- **Fix:** Divide all mm values by 10

### Add-in won't install
- Folder structure is wrong
- **Fix:** The add-in folder must contain both `.py` and `.manifest` files

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## License

MIT License - see LICENSE file.

---

## Credits

- MCP Server & Add-in developed with Claude AI (Anthropic)
- Uses the [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- Built for [Autodesk Fusion 360](https://www.autodesk.com/products/fusion-360/)