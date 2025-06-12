#!/usr/bin/env python3
"""
Cube-Cube CSG Difference Test
Test for cutting holes into cubes
"""

import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from marimo_openscad import openscad_viewer
    from solid2 import cube, difference

    mo.md("# ✂️ Cube Difference CSG Test")
    return cube, difference, mo, openscad_viewer


@app.cell
def _(mo):
    # Parameters for progressive difference test
    main_cube_size = mo.ui.slider(15, 25, value=20, label="Hauptwürfel Größe")
    hole_size = mo.ui.slider(2, 18, value=8, label="Bohrung Durchmesser") 

    mo.md(f"""
    **Test: Progressive Cube Difference (Bohrung durch den ganzen Würfel!)**

    {main_cube_size}
    {hole_size}

    **Anleitung:** 
    - Die Bohrung geht immer komplett durch den Würfel (X-Richtung)
    - Verändere die Bohrungsgröße von klein bis groß
    - Bei großer Bohrung: Fast der ganze Würfel wird ausgehöhlt
    """)
    return hole_size, main_cube_size


@app.cell
def _(cube, difference, hole_size, main_cube_size, openscad_viewer):
    # Create main cube (centered at origin)
    main_cube = cube([main_cube_size.value, main_cube_size.value, main_cube_size.value])
    
    # Create hole cube that goes completely through the main cube
    # Make hole cube longer than main cube to ensure it goes all the way through
    hole_length = main_cube_size.value + 5  # 5 units longer to ensure complete penetration
    hole_cube = cube([hole_length, hole_size.value, hole_size.value])
    
    # Center the hole cube in Y and Z, but let it extend through in X
    hole_positioned = hole_cube.translate([0, 0, 0])  # Centered at origin

    # Create difference: main_cube - hole_cube
    model = difference()(main_cube, hole_positioned)

    # Debug: Show generated SCAD code
    scad_code = model.as_scad() if hasattr(model, 'as_scad') else str(model)

    # Create viewer
    viewer = openscad_viewer(model, renderer_type="wasm")
    
    return model, scad_code, viewer


@app.cell
def _(mo, scad_code, main_cube_size, hole_size):
    # Extract values for safe access
    main_size = main_cube_size.value
    hole_diameter = hole_size.value
    
    # Show status based on hole size relative to main cube
    hole_ratio = hole_diameter / main_size
    if hole_ratio < 0.2:
        status = "🔲 Kleine Bohrung"
    elif hole_ratio < 0.5:
        status = "🕳️ Mittlere Bohrung"
    elif hole_ratio < 0.8:
        status = "🕳️ Große Bohrung"
    else:
        status = "⚪ Fast komplett ausgehöhlt"

    mo.md(f"""
    **Model:** {main_size}³ cube - {hole_diameter}×{hole_diameter} Bohrung → {status}

    **🔍 Generated SCAD Code:**
    ```openscad
    {scad_code}
    ```
    """)
    return status,


@app.cell
def _(viewer):
    # Display viewer
    viewer
    return


@app.cell
def _(mo):
    mo.md(
        """
    ## 🔍 Progressive Difference Test Instructions

    **So testest du die Difference-Funktion:**

    1. **Beginne mit kleiner Bohrung (2-4):** Du solltest ein kleines quadratisches Loch durch den Würfel sehen 🔲
    2. **Erhöhe auf mittlere Größe (~8):** Deutliches Loch durch den ganzen Würfel 🕳️
    3. **Erhöhe auf große Größe (~15):** Fast der ganze Würfel wird ausgehöhlt ⚪
    4. **Maximum (~18):** Nur noch dünne Wände bleiben übrig

    **✅ CSG Difference funktioniert wenn:**
    - **Sauberes quadratisches Loch** durch den kompletten Würfel
    - **Glatte Innenwände** im Loch sichtbar
    - **Korrekte Hohlraum-Geometrie** ohne Artefakte
    - Man kann **durch das Loch blicken**

    **❌ CSG Difference funktioniert NICHT wenn:**
    - Immer zwei separate Objekte (auch bei Überlappung)
    - Durchdringende Geometrie ohne Schnitt
    - Transparente Fallback-Visualisierung
    - Löcher werden nicht geschnitten
    """
    )
    return


if __name__ == "__main__":
    app.run()