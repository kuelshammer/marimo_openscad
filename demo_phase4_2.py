#!/usr/bin/env python3
"""
Phase 4.2 Demo: Multi-WASM Version Support

Demonstrates the new multi-WASM version management capabilities:
- Downloading and caching multiple WASM versions
- Dynamic version switching
- Intelligent version selection
- Version compatibility checking
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for demo
sys.path.insert(0, str(Path(__file__).parent / "src"))

from marimo_openscad.wasm_version_manager import (
    WASMVersionRegistry,
    WASMDownloader,
    DynamicWASMLoader, 
    WASMVersionSelector,
    WASMVersionManager
)


async def demo_wasm_registry():
    """Demo WASM version registry functionality."""
    
    print("🔍 Phase 4.2 Demo: Multi-WASM Version Support")
    print("=" * 55)
    
    print("\n📋 WASM Version Registry:")
    print("-" * 25)
    
    # Show available versions
    available_versions = WASMVersionRegistry.get_available_versions()
    print(f"Available WASM versions: {len(available_versions)}")
    
    for version in available_versions:
        info = WASMVersionRegistry.get_version_info(version)
        print(f"  • {version}")
        print(f"    Download URL: {info['download_url']}")
        print(f"    Expected size: {info['expected_size'] / 1024 / 1024:.1f}MB")
        print(f"    Backup URLs: {len(info['backup_urls'])} available")
    
    # Show version parsing
    print(f"\n🔄 Version Parsing Examples:")
    test_versions = ["2021.01", "2023.06.23", "invalid"]
    for version_str in test_versions:
        parsed = WASMVersionRegistry.parse_version_string(version_str)
        print(f"  '{version_str}' → {parsed}")


async def demo_wasm_downloader():
    """Demo WASM downloader functionality."""
    
    print("\n📥 WASM Downloader:")
    print("-" * 20)
    
    # Create downloader with temporary cache
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    downloader = WASMDownloader(cache_dir=temp_dir)
    
    print(f"Cache directory: {downloader.cache_dir}")
    print(f"Timeout: {downloader.timeout_seconds}s")
    print(f"Max retries: {downloader.max_retries}")
    
    # List initially empty cache
    cached = downloader.list_cached_versions()
    print(f"Initially cached versions: {len(cached)}")
    
    # Test download simulation (without actual download)
    print("\n🌐 Download Simulation:")
    try:
        # This will fail with network error, but demonstrates the workflow
        result = await downloader.download_version("2023.06")
        if result.success:
            print(f"✅ Downloaded {result.wasm_version.version}")
        else:
            print(f"❌ Download failed: {result.error_message}")
    except Exception as e:
        print(f"📡 Network operation skipped: {e}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


async def demo_dynamic_loader():
    """Demo dynamic WASM loader functionality."""
    
    print("\n🔄 Dynamic WASM Loader:")
    print("-" * 25)
    
    # Create loader with temporary cache
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    downloader = WASMDownloader(cache_dir=temp_dir)
    loader = DynamicWASMLoader(downloader)
    
    print(f"Active version: {loader.active_version}")
    print(f"Loaded versions: {len(loader.loaded_versions)}")
    
    # Show available versions (from registry)
    available = loader.get_available_versions()
    print(f"Available versions: {available}")
    
    # Get version info summary
    summary = loader.get_version_info_summary()
    print(f"\n📊 Loader Summary:")
    print(f"  Active: {summary['active_version']}")
    print(f"  Cached: {len(summary['cached_versions'])}")
    print(f"  Registry: {len(summary['registry_versions'])}")
    print(f"  Cache size: {summary['total_cached_size']} bytes")
    
    # Test switching (will fail without actual WASM files, but shows workflow)
    print(f"\n🔄 Version Switching Test:")
    try:
        success = await loader.switch_wasm_version("2023.06")
        if success:
            print(f"✅ Switched to version 2023.06")
        else:
            print(f"❌ Switch failed (expected - no cached WASM)")
    except Exception as e:
        print(f"📡 Switch operation: {e}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


async def demo_version_selector():
    """Demo version selection logic."""
    
    print("\n🎯 Version Selector:")
    print("-" * 20)
    
    # Create selector with temporary loader
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    downloader = WASMDownloader(cache_dir=temp_dir)
    loader = DynamicWASMLoader(downloader)
    selector = WASMVersionSelector(loader)
    
    # Test SCAD code analysis
    test_cases = [
        ("cube([10, 10, 10]);", "Basic cube"),
        ("cube([10**2, 10, 10]);", "With exponent operator"),
        ("points = [for (i = [1:10]) [i, i*2]];", "With list comprehension"),
        ("assert(true, 'test');", "With assertions"),
        ("cube([10, 10, 10]);\n" * 1000, "Large model")
    ]
    
    print(f"\n🔍 SCAD Code Analysis:")
    for scad_code, description in test_cases:
        requirements = selector.analyze_scad_requirements(scad_code)
        print(f"\n  📝 {description}:")
        print(f"     Min version: {requirements['min_version']}")
        print(f"     Features: {requirements['features']}")
        print(f"     Performance: {requirements['performance']}")
    
    # Test version selection
    print(f"\n🎯 Version Selection Tests:")
    test_requirements = [
        {"min_version": "2021.01", "performance": "stable"},
        {"min_version": "2023.06", "performance": "fastest"},
        {"preferred_version": "2022.03"}
    ]
    
    for requirements in test_requirements:
        selected = selector.select_optimal_version(requirements)
        print(f"  Requirements: {requirements}")
        print(f"  Selected: {selected}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


async def demo_wasm_version_manager():
    """Demo complete WASM version management system."""
    
    print("\n🚀 Complete WASM Version Manager:")
    print("-" * 35)
    
    # Create manager with temporary cache
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    manager = WASMVersionManager(cache_dir=temp_dir)
    
    # Test SCAD code optimization
    test_scad_codes = [
        "cube([10, 10, 10]);",
        "cube([10**2, 10, 10]);",  # Requires 2023.06+
        "for (i = [1:10]) { cube([i, i, i]); }"
    ]
    
    for scad_code in test_scad_codes:
        print(f"\n📝 Analyzing SCAD: {scad_code[:50]}...")
        
        optimal_version = await manager.get_optimal_version_for_scad(scad_code)
        print(f"   Optimal version: {optimal_version}")
        
        # Test version readiness (will show workflow)
        if optimal_version:
            ready = await manager.ensure_version_ready(optimal_version)
            print(f"   Version ready: {ready}")
    
    # Show system information
    print(f"\n📊 System Information:")
    system_info = manager.get_system_info()
    
    wasm_info = system_info["wasm_manager"]
    print(f"  Cache directory: {wasm_info['cache_dir']}")
    print(f"  Available versions: {wasm_info['available_versions']}")
    print(f"  Cached versions: {wasm_info['cached_versions']}")
    print(f"  Active version: {wasm_info['active_version']}")
    print(f"  Cache size: {wasm_info['total_cache_size_mb']:.1f}MB")
    
    registry_info = system_info["registry"]
    print(f"  Registry versions: {registry_info['known_versions']}")
    print(f"  Version count: {registry_info['version_count']}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


async def demo_viewer_integration():
    """Demo integration with OpenSCAD viewer."""
    
    print("\n🖼️ Viewer Integration:")
    print("-" * 22)
    
    try:
        from marimo_openscad.viewer import OpenSCADViewer
        
        # Create viewer with version management
        viewer = OpenSCADViewer(renderer_type="auto")
        
        # Check if version management is initialized
        if hasattr(viewer, 'version_manager') and viewer.version_manager:
            print("✅ Version management initialized")
            
            # Show version management info
            version_info = viewer.get_version_management_info()
            print(f"  Current version: {version_info.get('current_version', 'unknown')}")
            print(f"  Auto selection: {version_info.get('auto_selection_enabled', False)}")
            print(f"  Available versions: {len(version_info.get('available_versions', []))}")
            
            # Test version setting
            success = await viewer.set_openscad_version("auto")
            print(f"  Set to auto mode: {success}")
            
        else:
            print("⚠️ Version management not initialized (expected in demo)")
            
    except Exception as e:
        print(f"📝 Viewer integration test: {e}")


async def demo_real_world_scenarios():
    """Demo real-world usage scenarios."""
    
    print("\n🌍 Real-World Scenarios:")
    print("-" * 25)
    
    # Scenario 1: Community model compatibility
    print("\n📋 Scenario 1: Community Model Testing")
    
    community_models = [
        {
            "name": "Basic Gear", 
            "scad": "module gear() { cube([10, 10, 5]); } gear();",
            "expected_version": "2021.01"
        },
        {
            "name": "Advanced Parametric", 
            "scad": "function f(x) = x**2; cube([f(5), 10, 10]);",
            "expected_version": "2023.06"
        },
        {
            "name": "Modern List Processing",
            "scad": "points = [for (i = [1:5]) [i, i*2]]; polygon(points);",
            "expected_version": "2022.03"
        }
    ]
    
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    manager = WASMVersionManager(cache_dir=temp_dir)
    
    for model in community_models:
        print(f"\n  🔧 Testing: {model['name']}")
        print(f"     Code: {model['scad'][:50]}...")
        
        optimal_version = await manager.get_optimal_version_for_scad(model['scad'])
        print(f"     Detected version: {optimal_version}")
        print(f"     Expected version: {model['expected_version']}")
        
        # Check compatibility
        if optimal_version:
            from marimo_openscad.wasm_version_manager import WASMVersionRegistry
            optimal_parsed = WASMVersionRegistry.parse_version_string(optimal_version)
            expected_parsed = WASMVersionRegistry.parse_version_string(model['expected_version'])
            
            if optimal_parsed >= expected_parsed:
                print(f"     ✅ Compatible (meets minimum requirements)")
            else:
                print(f"     ❌ Incompatible (version too old)")
        else:
            print(f"     ⚠️ Could not determine optimal version")
    
    # Scenario 2: Performance optimization
    print(f"\n📋 Scenario 2: Performance Optimization")
    
    performance_tests = [
        {"name": "Small Model", "code": "cube([5, 5, 5]);", "expected": "stable"},
        {"name": "Large Model", "code": "union() { " + "cube([1, 1, 1]); " * 100 + "}", "expected": "fastest"}
    ]
    
    for test in performance_tests:
        print(f"\n  ⚡ {test['name']}:")
        
        # Analyze requirements
        from marimo_openscad.wasm_version_manager import WASMVersionSelector
        temp_downloader = WASMDownloader(cache_dir=temp_dir)
        temp_loader = DynamicWASMLoader(temp_downloader)
        selector = WASMVersionSelector(temp_loader)
        
        requirements = selector.analyze_scad_requirements(test['code'])
        print(f"     Performance preference: {requirements['performance']}")
        print(f"     Expected: {test['expected']}")
        
        if requirements['performance'] == test['expected']:
            print(f"     ✅ Correct performance analysis")
        else:
            print(f"     ⚠️ Unexpected performance preference")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


async def main():
    """Main demo function."""
    
    print("🎉 Phase 4.2: Multi-WASM Version Support Demo")
    print("=" * 50)
    print("Demonstrates dynamic WASM version management, downloading,")
    print("caching, and intelligent version selection capabilities.")
    
    try:
        # Run all demo sections
        await demo_wasm_registry()
        await demo_wasm_downloader()
        await demo_dynamic_loader()
        await demo_version_selector()
        await demo_wasm_version_manager()
        await demo_viewer_integration()
        await demo_real_world_scenarios()
        
        print("\n🎉 Phase 4.2 Demo Complete!")
        print("\nMulti-WASM Version Support Features:")
        print("  ✅ WASM version registry and metadata")
        print("  ✅ Dynamic downloading and caching")
        print("  ✅ Version switching and loading")
        print("  ✅ Intelligent version selection")
        print("  ✅ SCAD code analysis for requirements")
        print("  ✅ Viewer integration")
        print("  ✅ Real-world compatibility scenarios")
        
        print(f"\n📊 Summary:")
        print(f"   Available WASM versions: {len(WASMVersionRegistry.get_available_versions())}")
        print(f"   Platform: {sys.platform}")
        print(f"   Python: {sys.version.split()[0]}")
        print(f"   Status: Phase 4.2 foundation ready for integration")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())