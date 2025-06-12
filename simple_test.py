import marimo

__generated_with = "0.13.15"
app = marimo.App()


@app.cell
def __():
    import marimo as mo
    return mo,


@app.cell
def __(mo):
    mo.md("# Simple Import Test")
    return


@app.cell
def __(mo):
    # Test basic imports first
    import sys
    mo.md(f"**Python:** {sys.executable}")
    return sys,


@app.cell
def __(mo):
    try:
        import solid2
        mo.md("✅ solid2 imported successfully")
        success = True
    except Exception as e:
        mo.md(f"❌ solid2 import failed: {e}")
        success = False
    return solid2 if success else None, success


@app.cell
def __(mo):
    try:
        from marimo_openscad import openscad_viewer
        mo.md("✅ marimo_openscad imported successfully")
        viewer_imported = True
    except Exception as e:
        mo.md(f"❌ marimo_openscad import failed: {e}")
        openscad_viewer = None
        viewer_imported = False
    return openscad_viewer, viewer_imported


@app.cell
def __(mo, openscad_viewer, viewer_imported, solid2):
    if viewer_imported and openscad_viewer and solid2:
        try:
            model = solid2.cube([5, 5, 5])
            viewer = openscad_viewer(model, renderer_type="auto")
            mo.md("✅ Basic viewer creation works")
            test_successful = True
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            mo.md(f"❌ Viewer creation failed:\n```\n{error_details}\n```")
            model = None
            viewer = None
            test_successful = False
    else:
        mo.md("⚠️ Skipping viewer test - imports failed")
        model = None
        viewer = None
        test_successful = False
    return model, viewer, test_successful


if __name__ == "__main__":
    app.run()