import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    mo.md("# 🐛 Debug: JavaScript Error Analysis")
    return mo,


@app.cell
def _(mo):
    # Test minimal JavaScript first
    import anywidget
    import traitlets
    
    class DebugWidget(anywidget.AnyWidget):
        test_value = traitlets.Unicode("test").tag(sync=True)
        
        _esm = """
        function render({ model, el }) {
            el.innerHTML = '<div>✅ Minimal JS Widget Working</div>';
            console.log('Debug widget loaded successfully');
        }
        export default { render };
        """
    
    debug_widget = DebugWidget()
    debug_widget
    return DebugWidget, anywidget, debug_widget, traitlets


@app.cell
def _(mo):
    mo.md("## Test Complex JavaScript")
    return


@app.cell  
def _(anywidget, traitlets):
    # Test complex async JavaScript
    class AsyncDebugWidget(anywidget.AnyWidget):
        status = traitlets.Unicode("initializing").tag(sync=True)
        
        _esm = """
        async function render({ model, el }) {
            try {
                el.innerHTML = '<div id="status">Loading async test...</div>';
                const statusEl = el.querySelector('#status');
                
                // Test async operations
                await new Promise(resolve => setTimeout(resolve, 100));
                statusEl.innerHTML = '✅ Async JavaScript Working';
                
                console.log('Async debug widget loaded successfully');
            } catch (error) {
                console.error('Async debug error:', error);
                el.innerHTML = '<div style="color: red;">❌ Async Error: ' + error.message + '</div>';
            }
        }
        export default { render };
        """
    
    async_debug = AsyncDebugWidget()
    async_debug
    return AsyncDebugWidget, async_debug


@app.cell
def _(mo):
    mo.md("## Test OpenSCAD Viewer")
    return


@app.cell
def _():
    # Only now test our actual viewer
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(".").absolute() / "src"))
    
    from marimo_openscad import openscad_viewer
    from solid2 import cube
    return Path, cube, openscad_viewer, sys


@app.cell
def _(cube, openscad_viewer):
    # Test actual openscad viewer
    test_cube = cube([5, 5, 5])
    viewer = openscad_viewer(test_cube, renderer_type="auto")
    viewer
    return test_cube, viewer


if __name__ == "__main__":
    app.run()