# Installation Guide

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Browser**: Modern browser with WebGL support (Chrome, Firefox, Safari, Edge)

## Step 1: Install Python Dependencies

```bash
pip install marimo solidpython2 anywidget
```

### Package Versions
- `marimo >= 0.13.0` - Reactive notebook environment
- `solidpython2 >= 1.0.0` - Python interface to OpenSCAD
- `anywidget >= 0.9.0` - Widget framework for custom visualizations

## Step 2: Install OpenSCAD

OpenSCAD is required as a system dependency for 3D model rendering.

### Windows
1. Download OpenSCAD from [openscad.org](https://openscad.org/downloads.html)
2. Install using the Windows installer
3. Add OpenSCAD to your PATH, or place `openscad.exe` in your project directory

### macOS
**Option 1: Homebrew (Recommended)**
```bash
brew install openscad
```

**Option 2: Download App**
1. Download OpenSCAD.app from [openscad.org](https://openscad.org/downloads.html)
2. Place in `/Applications/`
3. The system will auto-detect the installation

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install openscad
```

### Linux (Other Distributions)
- **Fedora**: `sudo dnf install openscad`
- **Arch**: `sudo pacman -S openscad`
- **CentOS/RHEL**: Install from EPEL repository

## Step 3: Verify Installation

Create a test file `test_installation.py`:

```python
import marimo as mo
from solid2 import cube
from marimo_openscad import InteractiveViewer

# Test SolidPython2
model = cube(10)
print("✅ SolidPython2 working")

# Test viewer creation
viewer = InteractiveViewer()
print("✅ InteractiveViewer created")

print("🎉 Installation successful!")
```

Run the test:
```bash
python test_installation.py
```

## Step 4: Run Examples

Start with the basic shapes demo:
```bash
marimo edit examples/basic_shapes.py
```

Or try the castle demo:
```bash
marimo edit examples/castle_demo.py
```

## Troubleshooting

### OpenSCAD Not Found
**Error**: `OpenSCAD executable not found`

**Solutions**:
1. Ensure OpenSCAD is installed and in your PATH
2. Place the `openscad` executable in your project root directory
3. Specify the path manually:
```python
from marimo_openscad import OpenSCADRenderer
renderer = OpenSCADRenderer(openscad_path="/path/to/openscad")
```

### Three.js Loading Issues
**Error**: Widget shows "Failed to load Three.js"

**Solutions**:
1. Check your internet connection (Three.js loads from CDN)
2. Ensure browser has WebGL support
3. Try a different browser
4. Check browser console for detailed error messages

### Performance Issues
**Symptoms**: Slow 3D rendering, browser freezing

**Solutions**:
1. Reduce model complexity
2. Close other browser tabs
3. Use a computer with dedicated graphics card
4. The system automatically limits STL models to 2000 triangles for performance

### Import Errors
**Error**: `ModuleNotFoundError`

**Solutions**:
1. Ensure all dependencies are installed: `pip install marimo solidpython2 anywidget`
2. Check Python version: `python --version` (must be 3.8+)
3. Verify virtual environment activation if using one

## Development Setup

For development or contributing:

1. Clone the repository
2. Install in development mode:
```bash
cd marimo-openscad-clean
pip install -e src/
```

3. Run examples:
```bash
marimo edit examples/castle_demo.py
```

## Next Steps

- Read the [API Reference](api.md) to understand the available functions
- Explore the [Architecture Overview](architecture.md) to understand how the system works
- Check out more [Examples](../examples/) for inspiration