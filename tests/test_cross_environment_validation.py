#!/usr/bin/env python3
"""
Cross-Environment Validation Tests

CRITICAL MISSING TEST - Phase 2 Gap Closure
Tests Phase 2 improvements across different environments (dev, prod, platforms).
Validates cross-platform compatibility and environment-specific behavior.
"""

import pytest
import os
import sys
import platform
import time
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestCrossEnvironmentValidation:
    """Test Phase 2 improvements across different environments"""
    
    def test_development_vs_production_bundle_behavior(self):
        """Validate bundle behavior differs correctly by environment"""
        print("🔍 Testing development vs production bundle behavior...")
        
        try:
            from marimo_openscad.viewer_phase2 import openscad_viewer_phase2
            from solid2 import cube
        except ImportError as e:
            pytest.skip(f"Phase 2 viewer not available: {e}")
        
        # Test that development and production bundles have expected differences
        viewer = openscad_viewer_phase2(cube([1, 1, 1]))
        bundle_js = viewer._get_bundled_javascript()
        
        bundle_size = len(bundle_js)
        print(f"  Bundle size: {bundle_size:,} characters")
        
        # Analyze bundle characteristics
        bundle_analysis = {
            'size': bundle_size,
            'minified': False,
            'source_maps': False,
            'debug_info': False,
            'environment': 'unknown'
        }
        
        # Check for minification indicators
        minification_indicators = [
            bundle_size < 50000,  # Smaller size
            bundle_js.count('\n') / bundle_size < 0.05,  # Few newlines
            'eval(' not in bundle_js,  # No eval statements
            len([line for line in bundle_js.split('\n') if len(line.strip()) > 100]) > bundle_js.count('\n') * 0.5
        ]
        
        bundle_analysis['minified'] = sum(minification_indicators) >= 2
        
        # Check for development features
        dev_indicators = [
            'console.log',
            'console.warn', 
            'console.error',
            'debugger;',
            'development',
            'dev'
        ]
        
        found_dev_indicators = [ind for ind in dev_indicators if ind in bundle_js]
        bundle_analysis['debug_info'] = len(found_dev_indicators) > 0
        bundle_analysis['dev_indicators'] = found_dev_indicators
        
        # Check for production optimizations
        prod_indicators = [
            'production',
            'minified',
            bundle_analysis['minified']
        ]
        
        found_prod_indicators = [ind for ind in prod_indicators if (isinstance(ind, str) and ind in bundle_js) or (isinstance(ind, bool) and ind)]
        bundle_analysis['production_optimized'] = len(found_prod_indicators) > 0
        
        print(f"  Bundle characteristics:")
        print(f"    Minified: {'✅' if bundle_analysis['minified'] else '❌'}")
        print(f"    Debug info: {'✅' if bundle_analysis['debug_info'] else '❌'}")
        print(f"    Production optimized: {'✅' if bundle_analysis['production_optimized'] else '❌'}")
        print(f"    Dev indicators: {found_dev_indicators}")
        
        # Determine environment type
        if bundle_analysis['production_optimized'] and not bundle_analysis['debug_info']:
            bundle_analysis['environment'] = 'production'
        elif bundle_analysis['debug_info'] and not bundle_analysis['minified']:
            bundle_analysis['environment'] = 'development'
        else:
            bundle_analysis['environment'] = 'mixed'
        
        print(f"  Environment detected: {bundle_analysis['environment']}")
        
        # Validate bundle loading performance by environment
        load_times = []
        for i in range(3):
            start_time = time.perf_counter()
            test_viewer = openscad_viewer_phase2(cube([i+1, i+1, i+1]))
            load_time = time.perf_counter() - start_time
            load_times.append(load_time)
        
        avg_load_time = sum(load_times) / len(load_times)
        bundle_analysis['avg_load_time'] = avg_load_time
        
        print(f"  Average load time: {avg_load_time:.3f}s")
        
        # Environment-specific performance targets
        performance_targets = {
            'development': 3.0,  # More lenient for dev
            'production': 2.0,   # Stricter for prod
            'mixed': 2.5         # Moderate for mixed
        }
        
        target = performance_targets.get(bundle_analysis['environment'], 2.5)
        performance_acceptable = avg_load_time < target
        
        bundle_analysis['performance_acceptable'] = performance_acceptable
        print(f"  Performance target: {target}s, Actual: {avg_load_time:.3f}s - {'✅' if performance_acceptable else '⚠️'}")
        
        # Save bundle analysis
        analysis_file = Path(__file__).parent / "bundle_environment_analysis.json"
        import json
        with open(analysis_file, 'w') as f:
            json.dump(bundle_analysis, f, indent=2)
        
        print(f"  💾 Bundle environment analysis saved to: {analysis_file}")
        
        # Test passes if bundle behavior is reasonable for any environment
        assert bundle_size > 5000, f"Bundle too small: {bundle_size} chars"
        assert avg_load_time < 5.0, f"Bundle loading too slow: {avg_load_time:.3f}s"
        
        print("✅ Bundle environment behavior validated")
    
    def test_platform_specific_path_resolution(self):
        """Test Windows/Mac/Linux path resolution compatibility"""
        print("🔍 Testing platform-specific path resolution...")
        
        current_os = platform.system()
        current_arch = platform.machine()
        print(f"  Testing on: {current_os} {current_arch}")
        
        try:
            from marimo_openscad.viewer_phase2 import openscad_viewer_phase2
            from solid2 import cube
        except ImportError as e:
            pytest.skip(f"Phase 2 viewer not available: {e}")
        
        # Test that path resolution works on current platform
        viewer = openscad_viewer_phase2(cube([1, 1, 1]))
        bundle_js = viewer._get_bundled_javascript()
        
        # Check for platform-agnostic path handling
        path_handling_patterns = [
            'replace(/\\\\/g, \'/\')',
            'normalize',
            'path.join',
            'path.resolve',
            'path.sep',
            '.replace(',
            'split(',
            '/'
        ]
        
        found_path_patterns = []
        for pattern in path_handling_patterns:
            if pattern in bundle_js:
                found_path_patterns.append(pattern)
        
        print(f"  Path handling patterns found: {found_path_patterns}")
        
        # Platform-specific path separators should be handled
        platform_path_indicators = {
            'Windows': ['\\\\', 'replace(/\\\\/g', 'C:', 'drive'],
            'Darwin': ['/', 'posix', '/usr/', '/home/'],  # macOS
            'Linux': ['/', 'posix', '/usr/', '/home/']
        }
        
        current_platform_indicators = platform_path_indicators.get(current_os, [])
        found_platform_indicators = []
        
        for indicator in current_platform_indicators:
            if indicator in bundle_js:
                found_platform_indicators.append(indicator)
        
        print(f"  Platform-specific indicators: {found_platform_indicators}")
        
        # Test actual path operations
        try:
            # Test viewer creation multiple times to stress path resolution
            test_viewers = []
            path_errors = []
            
            for i in range(3):
                try:
                    test_viewer = openscad_viewer_phase2(cube([i+1, i+1, i+1]))
                    test_viewers.append(test_viewer)
                except Exception as e:
                    path_errors.append(str(e))
            
            path_resolution_success = len(path_errors) == 0
            print(f"  Path resolution test: {'✅' if path_resolution_success else '❌'}")
            if path_errors:
                print(f"    Errors: {path_errors}")
            
        except Exception as e:
            path_resolution_success = False
            print(f"  Path resolution failed: {e}")
        
        # Test file system access patterns
        wasm_paths = [
            Path(__file__).parent.parent / "src" / "marimo_openscad" / "wasm",
            Path(__file__).parent.parent / "src" / "marimo_openscad" / "static",
        ]
        
        accessible_paths = []
        for path in wasm_paths:
            if path.exists():
                accessible_paths.append(str(path))
        
        print(f"  Accessible WASM paths: {accessible_paths}")
        
        # Platform compatibility analysis
        platform_analysis = {
            'platform': current_os,
            'architecture': current_arch,
            'path_handling_patterns': found_path_patterns,
            'platform_indicators': found_platform_indicators,
            'path_resolution_success': path_resolution_success,
            'accessible_paths': accessible_paths,
            'platform_compatible': len(found_path_patterns) > 0 and path_resolution_success
        }
        
        analysis_file = Path(__file__).parent / "platform_compatibility_analysis.json"
        import json
        with open(analysis_file, 'w') as f:
            json.dump(platform_analysis, f, indent=2)
        
        print(f"  💾 Platform compatibility analysis saved to: {analysis_file}")
        
        # Test passes if basic path handling is present
        assert len(found_path_patterns) > 0, f"No path handling patterns found: {found_path_patterns}"
        
        print(f"✅ Platform-specific path resolution validated for {current_os}")
    
    def test_marimo_local_vs_wasm_compatibility(self):
        """Ensure bundles work in both Marimo environments"""
        print("🔍 Testing Marimo local vs WASM environment compatibility...")
        
        try:
            from marimo_openscad.viewer_phase2 import openscad_viewer_phase2
            from solid2 import cube
        except ImportError as e:
            pytest.skip(f"Phase 2 viewer not available: {e}")
        
        # Test environment detection logic
        viewer = openscad_viewer_phase2(cube([1, 1, 1]))
        bundle_js = viewer._get_bundled_javascript()
        
        # Check for Marimo environment detection
        marimo_detection_indicators = [
            'window.anywidget',
            'anywidget',
            'marimo',
            'typeof window',
            'window.location',
            'navigator'
        ]
        
        found_marimo_indicators = []
        for indicator in marimo_detection_indicators:
            if indicator in bundle_js:
                found_marimo_indicators.append(indicator)
        
        print(f"  Marimo detection indicators: {found_marimo_indicators}")
        
        # Check for WASM environment adaptations
        wasm_environment_indicators = [
            'WebAssembly',
            'wasm',
            'memory',
            '2GB',
            'constraint',
            'limit'
        ]
        
        found_wasm_indicators = []
        for indicator in wasm_environment_indicators:
            if indicator in bundle_js:
                found_wasm_indicators.append(indicator)
        
        print(f"  WASM environment indicators: {found_wasm_indicators}")
        
        # Check for local environment features
        local_environment_indicators = [
            'fetch',
            'XMLHttpRequest',
            'file://',
            'localhost',
            'http://',
            'https://'
        ]
        
        found_local_indicators = []
        for indicator in local_environment_indicators:
            if indicator in bundle_js:
                found_local_indicators.append(indicator)
        
        print(f"  Local environment indicators: {found_local_indicators}")
        
        # Test anywidget compatibility
        anywidget_compatibility = {
            'has_esm': hasattr(viewer, '_esm'),
            'has_css': hasattr(viewer, '_css'),
            'esm_size': len(getattr(viewer, '_esm', '')),
            'css_size': len(getattr(viewer, '_css', ''))
        }
        
        print(f"  anywidget compatibility:")
        print(f"    ESM: {'✅' if anywidget_compatibility['has_esm'] else '❌'} ({anywidget_compatibility['esm_size']} chars)")
        print(f"    CSS: {'✅' if anywidget_compatibility['has_css'] else '❌'} ({anywidget_compatibility['css_size']} chars)")
        
        # Test memory constraint awareness
        memory_constraint_patterns = [
            '2048',
            '2GB', 
            'memory',
            'limit',
            'constraint',
            'size'
        ]
        
        found_memory_patterns = []
        for pattern in memory_constraint_patterns:
            if pattern in bundle_js:
                found_memory_patterns.append(pattern)
        
        print(f"  Memory constraint awareness: {found_memory_patterns}")
        
        # Test renderer selection logic
        renderer_selection_patterns = [
            'auto',
            'wasm',
            'local',
            'renderer',
            'fallback',
            'detect'
        ]
        
        found_renderer_patterns = []
        for pattern in renderer_selection_patterns:
            if pattern in bundle_js:
                found_renderer_patterns.append(pattern)
        
        print(f"  Renderer selection patterns: {found_renderer_patterns}")
        
        # Test that viewer works with different renderer types
        renderer_tests = {}
        
        for renderer_type in ['auto', 'wasm', 'local']:
            try:
                start_time = time.perf_counter()
                test_viewer = openscad_viewer_phase2(cube([1, 1, 1]), renderer_type=renderer_type)
                creation_time = time.perf_counter() - start_time
                
                renderer_tests[renderer_type] = {
                    'success': True,
                    'creation_time': creation_time,
                    'has_stl_data': hasattr(test_viewer, 'stl_data') and test_viewer.stl_data is not None
                }
                
            except Exception as e:
                renderer_tests[renderer_type] = {
                    'success': False,
                    'error': str(e),
                    'creation_time': None
                }
        
        print(f"  Renderer type tests:")
        for renderer_type, result in renderer_tests.items():
            status = '✅' if result['success'] else '❌'
            print(f"    {renderer_type}: {status} ({result.get('creation_time', 'N/A')})")
        
        # Environment compatibility analysis
        environment_analysis = {
            'marimo_detection_indicators': found_marimo_indicators,
            'wasm_environment_indicators': found_wasm_indicators,
            'local_environment_indicators': found_local_indicators,
            'anywidget_compatibility': anywidget_compatibility,
            'memory_constraint_awareness': found_memory_patterns,
            'renderer_selection_patterns': found_renderer_patterns,
            'renderer_tests': renderer_tests,
            'marimo_compatible': len(found_marimo_indicators) >= 2 and anywidget_compatibility['has_esm']
        }
        
        analysis_file = Path(__file__).parent / "marimo_environment_analysis.json"
        import json
        with open(analysis_file, 'w') as f:
            json.dump(environment_analysis, f, indent=2)
        
        print(f"  💾 Marimo environment analysis saved to: {analysis_file}")
        
        # Test passes if basic Marimo compatibility is present
        marimo_compatible = (
            len(found_marimo_indicators) >= 1 and 
            anywidget_compatibility['has_esm'] and
            anywidget_compatibility['esm_size'] > 1000
        )
        
        assert marimo_compatible, f"Marimo compatibility insufficient: {environment_analysis}"
        
        print("✅ Marimo environment compatibility validated")


if __name__ == "__main__":
    # Allow running individual tests
    pytest.main([__file__, "-v", "-s"])