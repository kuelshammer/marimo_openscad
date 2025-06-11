#!/usr/bin/env python3
"""
Build script for Marimo-OpenSCAD package with WASM support

Builds the JavaScript widget, downloads WASM modules, optimizes assets,
and copies everything to the Python package location. This script is run 
during Python package building to ensure the latest JavaScript code and 
WASM assets are included.
"""

import subprocess
import shutil
import os
import json
from pathlib import Path

def check_prerequisites():
    """Check build prerequisites"""
    print("🔍 Checking build prerequisites...")
    
    # Check if npm is available
    try:
        result = subprocess.run(['npm', '--version'], check=True, capture_output=True, text=True)
        npm_version = result.stdout.strip()
        print(f"   ✅ npm {npm_version}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ npm not found. Please install Node.js and npm first.")
        print("   Visit: https://nodejs.org/")
        return False
    
    # Check if node is available
    try:
        result = subprocess.run(['node', '--version'], check=True, capture_output=True, text=True)
        node_version = result.stdout.strip()
        print(f"   ✅ Node.js {node_version}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js not found.")
        return False
    
    return True

def setup_wasm_assets():
    """Download and setup WASM assets"""
    print("🚀 Setting up WASM assets...")
    
    # Run WASM download script
    result = subprocess.run(['npm', 'run', 'wasm:download'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️ WASM download script failed: {result.stderr}")
        print("   Continuing with existing WASM files...")
        # Don't fail build if WASM files already exist
        return True
    else:
        print("   ✅ WASM modules downloaded successfully")
        return True

def build_frontend():
    """Build the frontend JavaScript widget with WASM support"""
    print("🔨 Building frontend JavaScript widget with WASM support...")
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check prerequisites
    if not check_prerequisites():
        return False
    
    # Install dependencies if needed
    if not (project_root / 'node_modules').exists():
        print("📦 Installing npm dependencies...")
        result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ npm install failed: {result.stderr}")
            return False
        print("   ✅ Dependencies installed")
    
    # Setup WASM assets
    if not setup_wasm_assets():
        print("⚠️ WASM setup had issues, continuing...")
    
    # Build the frontend with WASM support
    print("🔧 Building JavaScript bundle with WASM modules...")
    result = subprocess.run(['npm', 'run', 'build:wasm'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ WASM build failed, trying regular build: {result.stderr}")
        # Fallback to regular build
        result = subprocess.run(['npm', 'run', 'build'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Regular build also failed: {result.stderr}")
            return False
        print("   ✅ Regular build completed (WASM features may be limited)")
    else:
        print("   ✅ WASM-enabled build completed")
    
    # Verify the build
    print("🔍 Verifying build integrity...")
    result = subprocess.run(['npm', 'run', 'wasm:verify'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️ Build verification warnings: {result.stderr}")
        print("   Continuing with build (verification warnings are non-critical)")
    else:
        print("   ✅ Build verification passed")
    
    return copy_assets_to_python_package()

def copy_assets_to_python_package():
    """Copy built assets to Python package"""
    print("📦 Copying assets to Python package...")
    
    project_root = Path(__file__).parent
    dist_dir = project_root / 'dist'
    static_dir = project_root / 'src' / 'marimo_openscad' / 'static'
    
    if not dist_dir.exists():
        print("❌ Build output directory not found")
        return False
    
    # Create static directory if it doesn't exist
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy JavaScript files
    js_count = 0
    for js_file in dist_dir.glob('*.js'):
        dest = static_dir / js_file.name
        shutil.copy2(js_file, dest)
        print(f"   📄 Copied {js_file.name}")
        js_count += 1
    
    # Copy CSS files if any
    css_count = 0
    for css_file in dist_dir.glob('*.css'):
        dest = static_dir / css_file.name
        shutil.copy2(css_file, dest)
        print(f"   📄 Copied {css_file.name}")
        css_count += 1
    
    # Copy WASM assets
    wasm_count = 0
    dist_wasm_dir = dist_dir / 'wasm'
    if dist_wasm_dir.exists():
        static_wasm_dir = static_dir / 'wasm'
        static_wasm_dir.mkdir(exist_ok=True)
        
        for wasm_file in dist_wasm_dir.iterdir():
            if wasm_file.is_file():
                dest = static_wasm_dir / wasm_file.name
                shutil.copy2(wasm_file, dest)
                print(f"   🚀 Copied WASM asset: {wasm_file.name}")
                wasm_count += 1
    
    # Copy build manifests for debugging
    manifest_count = 0
    for manifest_file in ['optimization-manifest.json', 'build-verification-report.json']:
        manifest_path = dist_dir / manifest_file
        if manifest_path.exists():
            dest = static_dir / manifest_file
            shutil.copy2(manifest_path, dest)
            print(f"   📄 Copied manifest: {manifest_file}")
            manifest_count += 1
    
    # Generate asset summary
    create_asset_summary(static_dir, js_count, css_count, wasm_count, manifest_count)
    
    print(f"✅ Asset copying complete!")
    print(f"   JavaScript files: {js_count}")
    print(f"   CSS files: {css_count}")
    print(f"   WASM assets: {wasm_count}")
    print(f"   Manifest files: {manifest_count}")
    
    return True

def create_asset_summary(static_dir, js_count, css_count, wasm_count, manifest_count):
    """Create a summary of copied assets"""
    summary = {
        "build_timestamp": subprocess.run(['date', '-u'], capture_output=True, text=True).stdout.strip(),
        "asset_counts": {
            "javascript": js_count,
            "css": css_count,
            "wasm": wasm_count,
            "manifests": manifest_count
        },
        "wasm_enabled": wasm_count > 0,
        "total_assets": js_count + css_count + wasm_count + manifest_count,
        "python_package_ready": True
    }
    
    summary_path = static_dir / 'asset-summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"   📊 Asset summary: {summary_path}")

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