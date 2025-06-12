#!/usr/bin/env python3
"""
WASM Browser Test Demo
Simple marimo notebook to test browser-native OpenSCAD WASM rendering
"""

import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from marimo_openscad import openscad_viewer
    from solid2 import cube, cylinder, sphere, difference, union
    import time

    mo.md("""
    # 🚀 WASM Browser Test Demo

    Testing browser-native OpenSCAD rendering with **zero dependencies**.
    No local OpenSCAD installation required!
    """)
    return cube, cylinder, difference, mo, openscad_viewer, sphere, time, union


@app.cell
def _(mo):
    mo.md("""## 📋 Renderer Status Check""")
    return


@app.cell
def _(Path, mo):
    # Check WASM availability
    from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer

    wasm_renderer = OpenSCADWASMRenderer()
    stats = wasm_renderer.get_stats()

    status_info = f"""
    **WASM Renderer Status:**
    - Available: {stats['is_available']}
    - WASM Files Found: {len(stats['wasm_files'])}
    - WASM Path: `{stats['wasm_path']}`

    **Bundled WASM Files:**
    """

    for filename, path in stats['wasm_files'].items():
        size_mb = Path(path).stat().st_size / 1024 / 1024
        status_info += f"\n- `{filename}`: {size_mb:.1f} MB"

    mo.md(status_info)
    return


@app.cell
def _(mo):
    from pathlib import Path

    mo.md("""
    ## 🎛️ Interactive Parameters
    """)
    return (Path,)


@app.cell
def _(mo):
    # Reactive parameters
    size = mo.ui.slider(10, 25, value=20, label="Big Cube Size")
    hole_radius = mo.ui.slider(2, 10, value=6, label="Small Cube Size (corner cutout)")
    renderer_type = mo.ui.radio(
        ["auto", "wasm", "local"], 
        value="wasm", 
        label="Renderer Type"
    )

    mo.md(f"""
    **Controls:**

    {size}
    {hole_radius} 
    {renderer_type}
    """)
    return hole_radius, renderer_type, size


@app.cell
def _(hole_radius, mo, size):
    mo.md(f"""## 🔄 Live Model - Corner Cut (Big: {size.value}, Small: {hole_radius.value})""")
    return


@app.cell
def _(
    cube,
    cylinder,
    difference,
    hole_radius,
    mo,
    openscad_viewer,
    renderer_type,
    size,
    time,
):
    # Create reactive 3D model - BIG cube minus SMALL corner cube
    big_cube = cube([size.value, size.value, size.value])
    small_cube = cube([hole_radius.value, hole_radius.value, hole_radius.value])
    
    # Position small cube at corner (translate to one corner)
    small_cube_positioned = small_cube.translate([0, 0, 0])  # At origin corner
    
    # Subtract small cube from big cube
    model = difference()(big_cube, small_cube_positioned)

    # Performance timing
    start_time = time.time()
    viewer = openscad_viewer(model, renderer_type=renderer_type.value)
    render_time = (time.time() - start_time) * 1000

    mo.md(f"**Render Time:** {render_time:.1f}ms")
    return (viewer,)


@app.cell
def _(viewer):
    # Display the viewer
    viewer
    return


@app.cell
def _(mo):
    mo.md("""## 🧪 Renderer Info""")
    return


@app.cell
def _(mo, viewer):
    # Get renderer information
    try:
        info = viewer.get_renderer_info()
        info_text = f"""
        **Active Renderer Info:**
        - Type: `{info.get('type', 'unknown')}`
        - Status: `{info.get('status', 'unknown')}`
        - WASM Enabled: {info.get('wasm_enabled', False)}
        - WASM Supported: {info.get('wasm_supported', False)}
        """

        if 'performance' in info:
            perf = info['performance']
            info_text += f"\n- Last Render: {perf.get('last_render_time', 'N/A')}ms"

    except Exception as e:
        info_text = f"**Renderer Info Error:** `{e}`"

    mo.md(info_text)
    return


@app.cell
def _(mo):
    mo.md("""## 🎯 Performance Test""")
    return


@app.cell
def _(cube, cylinder, difference, mo, openscad_viewer, sphere, time, union):
    # Performance comparison
    test_model = difference()(
        union()(
            cube([20, 20, 20]),
            sphere(r=12).translate([0, 0, 20])
        ),
        cylinder(r=6, h=40, center=True)
    )

    # Test different renderers
    results = {}

    for renderer_name in ["wasm", "auto"]:
        try:
            start = time.time()
            test_viewer = openscad_viewer(test_model, renderer_type=renderer_name)
            end = time.time()
            results[renderer_name] = f"{(end-start)*1000:.1f}ms"
        except Exception as e:
            results[renderer_name] = f"Error: {str(e)[:50]}"

    perf_text = "**Performance Comparison:**\n"
    for renderer_name, time_str in results.items():
        perf_text += f"\n- {renderer_name.upper()}: {time_str}"

    mo.md(perf_text)
    return


@app.cell
def _(mo):
    mo.md(
        """
    ## ✅ Browser Test Checklist

    **Manual Tests to Perform:**

    1. **🔄 Parameter Changes**: Move sliders - model should update instantly
    2. **🖱️ 3D Navigation**: Drag to rotate, scroll to zoom
    3. **⚡ Performance**: Check browser dev tools for WASM loading
    4. **🔍 Console**: Look for WASM-related logs in browser console
    5. **📱 Responsive**: Resize browser window
    6. **🔃 Renderer Switch**: Try different renderer types

    **Expected Browser Behavior:**
    - No OpenSCAD installation required
    - Instant parameter updates  
    - Smooth 3D interaction
    - WASM modules load from package
    - No server round-trips for rendering
    """
    )
    return


if __name__ == "__main__":
    app.run()
