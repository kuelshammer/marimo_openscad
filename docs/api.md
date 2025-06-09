# API Reference

## Core Classes

### `InteractiveViewer`

The main widget for displaying 3D models in Marimo notebooks.

```python
from marimo_openscad import InteractiveViewer

viewer = InteractiveViewer()
viewer.update_model(model)
viewer
```

#### Methods

**`update_model(model)`**
- **Description**: Update the 3D model displayed in the viewer
- **Parameters**: 
  - `model`: SolidPython2 object with `as_scad()` method
- **Returns**: None
- **Example**:
```python
from solid2 import cube, sphere
model = cube(20) + sphere(10).translate([10, 10, 20])
viewer.update_model(model)
```

**`save_stl(model, file_path)`**
- **Description**: Save the model as an STL file
- **Parameters**:
  - `model`: SolidPython2 object
  - `file_path`: String path where to save the STL file
- **Returns**: None
- **Example**:
```python
viewer.save_stl(model, "my_model.stl")
```

#### Traits (Reactive Properties)

**`stl_data`** (Unicode)
- **Description**: Base64-encoded STL data for the JavaScript viewer
- **Usage**: Automatically updated by `update_model()`, generally not accessed directly

### `OpenSCADRenderer`

Low-level interface to OpenSCAD command-line execution.

```python
from marimo_openscad import OpenSCADRenderer

renderer = OpenSCADRenderer()
stl_bytes = renderer.render_solidpython_to_stl(model)
```

#### Constructor

**`OpenSCADRenderer(openscad_path=None)`**
- **Parameters**:
  - `openscad_path` (optional): Path to OpenSCAD executable. If None, searches common locations.

#### Methods

**`render_solidpython_to_stl(model)`**
- **Description**: Render a SolidPython2 model to STL bytes
- **Parameters**:
  - `model`: SolidPython2 object with `as_scad()` method
- **Returns**: STL file contents as bytes
- **Raises**: `OpenSCADError` if rendering fails

**`render_scad_to_stl(scad_code)`**
- **Description**: Render OpenSCAD code to STL bytes
- **Parameters**:
  - `scad_code`: OpenSCAD code as string
- **Returns**: STL file contents as bytes
- **Raises**: `OpenSCADError` if rendering fails

### `SolidPythonBridge`

Enhanced bridge with caching and error handling.

```python
from marimo_openscad import SolidPythonBridge

bridge = SolidPythonBridge()
stl_bytes = bridge.render_to_stl(model)
```

#### Constructor

**`SolidPythonBridge(openscad_path=None)`**
- **Parameters**:
  - `openscad_path` (optional): Path to OpenSCAD executable

#### Methods

**`render_to_stl(model)`**
- **Description**: Render model to STL with automatic caching
- **Parameters**:
  - `model`: SolidPython2 object
- **Returns**: STL file contents as bytes
- **Features**: Automatic caching based on model content hash

**`save_model_to_stl(model, file_path)`**
- **Description**: Render and save model to STL file
- **Parameters**:
  - `model`: SolidPython2 object
  - `file_path`: String path for output file

**`clear_cache()`**
- **Description**: Clear the internal model cache
- **Returns**: None

## Exception Classes

### `OpenSCADError`

Raised when OpenSCAD execution fails.

**Common Causes**:
- OpenSCAD executable not found
- Invalid OpenSCAD code
- OpenSCAD crashes or times out

**Example Handling**:
```python
try:
    stl_data = renderer.render_solidpython_to_stl(model)
except OpenSCADError as e:
    print(f"OpenSCAD failed: {e}")
```

### `SolidPythonError`

Raised when SolidPython2 integration fails.

**Common Causes**:
- Invalid model object (missing `as_scad()` method)
- File I/O errors during STL saving

## Usage Patterns

### Basic 3D Visualization

```python
import marimo as mo
from solid2 import cube, cylinder
from marimo_openscad import InteractiveViewer

# Create model
model = cube(20) - cylinder(r=5, h=25, center=True)

# Display in 3D
viewer = InteractiveViewer()
viewer.update_model(model)
viewer
```

### Reactive Parameters

```python
import marimo as mo
from solid2 import cube, sphere
from marimo_openscad import InteractiveViewer

# Reactive controls
size = mo.ui.slider(10, 50, value=25, label="Size")
radius = mo.ui.slider(5, 20, value=10, label="Sphere Radius")

# Model updates automatically when sliders change
model = cube(size.value) + sphere(radius.value).translate([size.value/2, size.value/2, size.value])

# 3D viewer
viewer = InteractiveViewer()
viewer.update_model(model)
viewer
```

### Export to STL

```python
# Method 1: Using InteractiveViewer
viewer.save_stl(model, "output.stl")

# Method 2: Using SolidPython2 directly
model.save_as_scad("model.scad")  # Save OpenSCAD code

# Method 3: Using SolidPythonBridge
from marimo_openscad import SolidPythonBridge
bridge = SolidPythonBridge()
bridge.save_model_to_stl(model, "output.stl")
```

### Error Handling

```python
from marimo_openscad import InteractiveViewer, OpenSCADError, SolidPythonError

viewer = InteractiveViewer()

try:
    viewer.update_model(model)
except (OpenSCADError, SolidPythonError) as e:
    print(f"Rendering failed: {e}")
    # Handle error (show message, use fallback model, etc.)
```

### Custom OpenSCAD Path

```python
from marimo_openscad import InteractiveViewer, OpenSCADRenderer

# Specify custom OpenSCAD location
viewer = InteractiveViewer()
viewer.bridge = SolidPythonBridge(openscad_path="/custom/path/to/openscad")
```

## Widget Integration

### 3D Viewer Controls

The `InteractiveViewer` includes built-in mouse controls:

- **Mouse Drag**: Rotate camera around model
- **Mouse Wheel**: Zoom in/out
- **Automatic Centering**: Model is automatically centered in view
- **Progressive Fallback**: Shows colored cube if STL parsing fails

### Marimo Reactivity

The viewer integrates seamlessly with Marimo's reactive system:

```python
# These cells will automatically update when parameters change
@app.cell
def _(mo):
    height = mo.ui.slider(10, 100, value=50)
    return height,

@app.cell  
def _(height):
    model = cube([20, 20, height.value])
    return model,

@app.cell
def _(model):
    viewer = InteractiveViewer()
    viewer.update_model(model)
    return viewer,
```

## Performance Considerations

### Model Complexity

- STL models are limited to 2000 triangles for performance
- Complex models may render slowly in the browser
- Consider simplifying geometry for interactive use

### Caching

- `SolidPythonBridge` automatically caches rendered models
- Cache is based on OpenSCAD code content hash
- Use `clear_cache()` to free memory if needed

### Browser Resources

- WebGL rendering uses GPU resources
- Close unused viewer widgets to free memory
- Consider using smaller models for development/testing