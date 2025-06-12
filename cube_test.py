#!/usr/bin/env python3
"""
Cube-Cube CSG Test
Simple test for corner cut visualization
"""

import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from marimo_openscad import openscad_viewer
    from solid2 import cube, union

    mo.md("# 🔲 Cube Union CSG Test")
    return cube, mo, openscad_viewer, union


@app.cell
def _(mo):
    # Simple parameters for progressive union test
    cube1_size = mo.ui.slider(8, 20, value=12, label="Cube 1 Size")
    cube2_size = mo.ui.slider(8, 20, value=10, label="Cube 2 Size") 
    distance = mo.ui.slider(0, 25, value=15, label="Abstand zwischen Würfeln")

    mo.md(f"""
    **Test: Progressive Cube Union (Abstand verkleinern → Verschmelzung!)**

    {cube1_size}
    {cube2_size}
    {distance}

    **Anleitung:** Beginne mit Abstand = 25 (getrennt), dann verkleinere auf 0 (verschmolzen)
    """)
    return cube1_size, cube2_size, distance


@app.cell
def _(cube, cube1_size, cube2_size, distance, mo, openscad_viewer, union):
    # Create two cubes
    cube1 = cube([cube1_size.value, cube1_size.value, cube1_size.value])
    cube2 = cube([cube2_size.value, cube2_size.value, cube2_size.value])

    # Position cube2 based on distance slider
    # At distance=25: completely separate
    # At distance=0: completely overlapping (perfect union test!)
    cube2_positioned = cube2.translate([distance.value, 0, 0])

    # Union the cubes
    model = union()(cube1, cube2_positioned)

    # Debug: Show generated SCAD code
    scad_code = model.as_scad() if hasattr(model, 'as_scad') else str(model)

    # Create viewer
    viewer = openscad_viewer(model, renderer_type="wasm")

    # Show status based on distance
    if distance.value > cube1_size.value:
        status = "🔲 🔲 Getrennt (zwei separate Würfel)"
    elif distance.value > 0:
        status = "🔗 Berührend/Überlappend (sollten verschmelzen!)"
    else:
        status = "🟦 Komplett überlappt (ein Würfel)"

    mo.md(f"""
    **Model:** {cube1_size.value}³ cube ∪ {cube2_size.value}³ cube, Abstand: {distance.value} → {status}

    **🔍 Generated SCAD Code:**
    ```openscad
    {scad_code}
    ```
    """)
    return (viewer,)


@app.cell
def _(viewer):
    # Display viewer
    viewer
    return


@app.cell
def _(mo):
    mo.md(
        """
    ## 🔍 Progressive Union Test Instructions

    **So testest du die Union-Funktion:**

    1. **Beginne mit Abstand = 25:** Du solltest zwei getrennte Würfel sehen 🔲 🔲
    2. **Verkleinere Abstand auf ~12:** Würfel berühren sich → sollten **verbunden** werden 🔗
    3. **Verkleinere weiter auf 0:** Würfel überlappen komplett → sollte **ein Würfel** sein 🟦

    **✅ CSG Union funktioniert wenn:**
    - Bei Berührung/Überlappung: **Ein zusammenhängendes Objekt** (nicht zwei separate!)
    - **Glatte Verbindungen** ohne doppelte Flächen
    - **Kein Z-Fighting** in Überlappungszonen

    **❌ CSG Union funktioniert NICHT wenn:**
    - Immer zwei separate Würfel (auch bei Überlappung)
    - Durchdringende Geometrie sichtbar
    - Transparente Fallback-Visualisierung
    """
    )
    return


if __name__ == "__main__":
    app.run()
