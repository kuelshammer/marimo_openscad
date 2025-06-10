#!/usr/bin/env python3
"""
Build script for Marimo-OpenSCAD package

Builds the JavaScript widget and copies it to the Python package location.
This script is run during Python package building to ensure the latest
JavaScript code is included.
"""

import subprocess
import shutil
import os
from pathlib import Path

def build_frontend():
    """Build the frontend JavaScript widget"""
    print("🔨 Building frontend JavaScript widget...")
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check if npm is available
    try:
        subprocess.run(['npm', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ npm not found. Please install Node.js and npm first.")
        print("   Visit: https://nodejs.org/")
        return False
    
    # Install dependencies if needed
    if not (project_root / 'node_modules').exists():
        print("📦 Installing npm dependencies...")
        result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ npm install failed: {result.stderr}")
            return False
    
    # Build the frontend
    print("🔧 Building JavaScript bundle...")
    result = subprocess.run(['npm', 'run', 'build'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Build failed: {result.stderr}")
        return False
    
    # Copy built files to Python package
    dist_dir = project_root / 'dist'
    static_dir = project_root / 'src' / 'marimo_openscad' / 'static'
    
    if not dist_dir.exists():
        print("❌ Build output directory not found")
        return False
    
    # Create static directory if it doesn't exist
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy JS files
    for js_file in dist_dir.glob('*.js'):
        dest = static_dir / js_file.name
        shutil.copy2(js_file, dest)
        print(f"📄 Copied {js_file.name} to Python package")
    
    # Copy CSS files if any
    for css_file in dist_dir.glob('*.css'):
        dest = static_dir / css_file.name
        shutil.copy2(css_file, dest)
        print(f"📄 Copied {css_file.name} to Python package")
    
    print("✅ Frontend build complete!")
    return True

def clean_build():
    """Clean build artifacts"""
    print("🧹 Cleaning build artifacts...")
    
    project_root = Path(__file__).parent
    
    # Remove dist directory
    dist_dir = project_root / 'dist'
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("🗑️  Removed dist/")
    
    # Remove built files from Python package
    static_dir = project_root / 'src' / 'marimo_openscad' / 'static'
    if static_dir.exists():
        for file in static_dir.glob('widget.*.js'):
            file.unlink()
            print(f"🗑️  Removed {file.name}")
        for file in static_dir.glob('widget.*.css'):
            file.unlink()
            print(f"🗑️  Removed {file.name}")
    
    print("✅ Clean complete!")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean_build()
    else:
        success = build_frontend()
        sys.exit(0 if success else 1)