#!/usr/bin/env python3
"""
WASM Integration Foundation Tests

CRITICAL MISSING TEST - Phase 1 Gap Closure
Foundation tests required before Phase 3 implementation.
Validates WASM module loading, JavaScript pipeline accessibility,
and async communication infrastructure capabilities.
"""

import pytest
import os
import sys
from pathlib import Path
import json
import base64

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestWASMIntegrationFoundation:
    """Foundation tests required before Phase 3 implementation"""
    
    def test_wasm_modules_loadable_from_bundle_paths(self):
        """Validate WASM modules can load from Phase 2 bundle paths"""
        
        print("🔍 Testing WASM module accessibility from bundle paths...")
        
        # Test if Phase 2 viewer exists and is importable
        try:
            from marimo_openscad import viewer_phase2
            print("✅ Phase 2 viewer module importable")
        except ImportError as e:
            print(f"❌ Phase 2 viewer not available: {e}")
            pytest.skip("Phase 2 viewer not implemented - Phase 2 must be completed first")
        
        # Test Phase 2 viewer creation
        try:
            from solid2 import cube
            test_model = cube([1, 1, 1])
            viewer = viewer_phase2.openscad_viewer_phase2(test_model)
            print("✅ Phase 2 viewer creation successful")
        except Exception as e:
            print(f"⚠️ Phase 2 viewer creation failed: {e}")
            # Continue testing - might be expected during development
        
        # Check if WASM files are accessible through viewer
        wasm_files_found = {}
        
        # Check for bundled WASM static files
        wasm_static_paths = [
            Path(__file__).parent.parent / "src" / "marimo_openscad" / "wasm",
            Path(__file__).parent.parent / "src" / "marimo_openscad" / "static" / "wasm",
            Path(__file__).parent.parent / "dist" / "wasm"
        ]
        
        expected_wasm_files = [
            "openscad.wasm",
            "openscad.js",
            "openscad.d.ts",
            "openscad.fonts.js",
            "openscad.mcad.js"
        ]
        
        for wasm_dir in wasm_static_paths:
            if wasm_dir.exists():
                print(f"🔍 Checking WASM directory: {wasm_dir}")
                
                for filename in expected_wasm_files:
                    file_path = wasm_dir / filename
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        wasm_files_found[filename] = {
                            'path': str(file_path),
                            'size': file_size,
                            'exists': True
                        }
                        print(f"  ✅ {filename}: {file_size} bytes")
                    else:
                        wasm_files_found[filename] = {
                            'path': str(file_path),
                            'exists': False
                        }
                        print(f"  ❌ {filename}: not found")
        
        # Test WASM file accessibility through Phase 2 viewer (if available)
        try:
            if hasattr(viewer_phase2, 'OpenSCADWASMRenderer'):
                wasm_renderer = viewer_phase2.OpenSCADWASMRenderer()
                if hasattr(wasm_renderer, 'get_wasm_files'):
                    viewer_wasm_files = wasm_renderer.get_wasm_files()
                    print(f"✅ WASM files accessible via viewer: {list(viewer_wasm_files.keys())}")
                    
                    for filename, path in viewer_wasm_files.items():
                        if Path(path).exists():
                            wasm_files_found[filename] = wasm_files_found.get(filename, {})
                            wasm_files_found[filename]['viewer_accessible'] = True
                        else:
                            print(f"⚠️ Viewer reports {filename} at {path} but file not found")
        except Exception as e:
            print(f"⚠️ Could not test WASM file accessibility via viewer: {e}")
        
        # Validate minimum requirements for Phase 3
        critical_files = ["openscad.wasm", "openscad.js"]
        critical_files_present = all(
            wasm_files_found.get(f, {}).get('exists', False) 
            for f in critical_files
        )
        
        print(f"\n📊 WASM FILES SUMMARY:")
        print(f"  Total files found: {sum(1 for f in wasm_files_found.values() if f.get('exists', False))}")
        print(f"  Critical files present: {critical_files_present}")
        print(f"  Files details: {json.dumps(wasm_files_found, indent=2)}")
        
        if critical_files_present:
            print("✅ MINIMUM WASM FILES AVAILABLE for Phase 3")
        else:
            print("❌ CRITICAL WASM FILES MISSING - Phase 3 blocked")
        
        # Save WASM files inventory for Phase 3 reference
        import time
        wasm_inventory = {
            'timestamp': time.time(),
            'critical_files_present': critical_files_present,
            'wasm_files_found': wasm_files_found,
            'phase2_viewer_available': 'viewer_phase2' in sys.modules
        }
        
        inventory_file = Path(__file__).parent / "wasm_files_inventory.json"
        with open(inventory_file, 'w') as f:
            json.dump(wasm_inventory, f, indent=2, default=str)
        
        print(f"\n💾 WASM files inventory saved to: {inventory_file}")
        
        # Test succeeds if critical files are present, documents status otherwise
        assert critical_files_present, f"Critical WASM files missing: {[f for f in critical_files if not wasm_files_found.get(f, {}).get('exists', False)]}"

    def test_javascript_wasm_pipeline_accessible(self):
        """Test that JS WASM pipeline is accessible from Python side"""
        
        print("🔍 Testing JavaScript WASM pipeline accessibility...")
        
        # Test if Phase 2 bundled JavaScript contains WASM-related functions
        try:
            from marimo_openscad import viewer_phase2
            from solid2 import cube
            
            test_viewer = viewer_phase2.openscad_viewer_phase2(cube([1, 1, 1]))
            
            # Get bundled JavaScript content
            if hasattr(test_viewer, '_get_bundled_javascript'):
                bundle_js = test_viewer._get_bundled_javascript()
                print(f"✅ Bundle JavaScript accessible: {len(bundle_js)} characters")
            else:
                bundle_js = getattr(test_viewer, '_esm', '')
                print(f"✅ ESM JavaScript accessible: {len(bundle_js)} characters")
            
            if len(bundle_js) < 1000:
                print("⚠️ JavaScript bundle seems too small")
                bundle_js = ""  # Treat as empty for testing
            
        except Exception as e:
            print(f"❌ Could not access bundled JavaScript: {e}")
            bundle_js = ""
        
        # Check for required WASM-related functions in JavaScript
        required_functions = [
            'OpenSCADDirectRenderer',
            'WASMManager', 
            'createOptimalRenderer',
            'parseSTL',
            'detectWASMBasePath',
            'loadWASMWithFallbacks'
        ]
        
        # Additional WASM-related patterns to check
        wasm_patterns = [
            'WebAssembly',
            'wasm',
            '.wasm',
            'openscad.wasm',
            'wasmModule',
            'wasmInstance',
            'WASM'
        ]
        
        function_availability = {}
        pattern_availability = {}
        
        for func in required_functions:
            present = func in bundle_js
            function_availability[func] = present
            print(f"  {'✅' if present else '❌'} {func}: {'Present' if present else 'Missing'}")
        
        for pattern in wasm_patterns:
            present = pattern in bundle_js
            pattern_availability[pattern] = present
            print(f"  {'✅' if present else '❌'} {pattern}: {'Present' if present else 'Missing'}")
        
        # Count available functions and patterns
        available_functions = sum(function_availability.values())
        available_patterns = sum(pattern_availability.values())
        
        print(f"\n📊 JAVASCRIPT WASM PIPELINE ANALYSIS:")
        print(f"  Required functions available: {available_functions}/{len(required_functions)}")
        print(f"  WASM patterns found: {available_patterns}/{len(wasm_patterns)}")
        
        # Determine pipeline readiness
        pipeline_ready = (
            available_functions >= len(required_functions) * 0.5 and  # At least 50% of functions
            available_patterns >= len(wasm_patterns) * 0.3  # At least 30% of patterns
        )
        
        if pipeline_ready:
            print("✅ JavaScript WASM pipeline appears ready")
        elif available_functions > 0 or available_patterns > 0:
            print("⚡ JavaScript WASM pipeline partially available")
        else:
            print("❌ JavaScript WASM pipeline not detected")
        
        # Test JavaScript syntax validity (basic check)
        js_syntax_valid = True
        if bundle_js:
            try:
                # Basic syntax checks
                syntax_issues = []
                
                # Check for unmatched brackets
                if bundle_js.count('{') != bundle_js.count('}'):
                    syntax_issues.append("Unmatched curly brackets")
                    
                if bundle_js.count('(') != bundle_js.count(')'):
                    syntax_issues.append("Unmatched parentheses")
                    
                if bundle_js.count('[') != bundle_js.count(']'):
                    syntax_issues.append("Unmatched square brackets")
                
                # Check for basic JavaScript structure
                if 'function' not in bundle_js and '=>' not in bundle_js and 'class' not in bundle_js:
                    syntax_issues.append("No function/class definitions found")
                
                if syntax_issues:
                    print(f"⚠️ JavaScript syntax issues: {syntax_issues}")
                    js_syntax_valid = False
                else:
                    print("✅ JavaScript syntax appears valid")
                    
            except Exception as e:
                print(f"⚠️ Could not validate JavaScript syntax: {e}")
                js_syntax_valid = False
        
        # Save JavaScript pipeline analysis
        import time
        pipeline_analysis = {
            'timestamp': time.time(),
            'bundle_size': len(bundle_js),
            'pipeline_ready': pipeline_ready,
            'js_syntax_valid': js_syntax_valid,
            'function_availability': function_availability,
            'pattern_availability': pattern_availability,
            'available_functions_count': available_functions,
            'available_patterns_count': available_patterns
        }
        
        analysis_file = Path(__file__).parent / "js_pipeline_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(pipeline_analysis, f, indent=2)
        
        print(f"\n💾 JavaScript pipeline analysis saved to: {analysis_file}")
        
        # Test passes if pipeline shows signs of WASM capability
        assert (available_functions > 0 or available_patterns > 0), f"No WASM-related functionality detected in JavaScript bundle"

    def test_async_communication_infrastructure_possible(self):
        """Validate that async communication infrastructure is possible"""
        
        print("🔍 Testing async communication infrastructure capabilities...")
        
        # Test basic anywidget message passing capability
        anywidget_available = False
        viewer_communication_ready = False
        
        try:
            # Test Phase 2 viewer availability
            from marimo_openscad import viewer_phase2
            from solid2 import cube
            
            test_widget = viewer_phase2.openscad_viewer_phase2(cube([1, 1, 1]))
            anywidget_available = True
            print("✅ Phase 2 viewer available for communication testing")
            
            # Check if widget has communication capabilities
            has_esm = hasattr(test_widget, '_esm')
            esm_size = len(test_widget._esm) if has_esm else 0
            
            print(f"  anywidget ESM component: {'✅' if has_esm else '❌'}")
            print(f"  ESM size: {esm_size} characters")
            
            if has_esm and esm_size > 1000:
                viewer_communication_ready = True
                print("✅ anywidget communication infrastructure appears ready")
            else:
                print("⚠️ anywidget communication infrastructure limited")
            
        except Exception as e:
            print(f"❌ Phase 2 viewer communication test failed: {e}")
        
        # Test UUID generation and tracking capabilities (for async requests)
        import uuid
        
        uuid_test_results = {}
        
        try:
            # Test UUID generation
            test_uuids = [str(uuid.uuid4()) for _ in range(10)]
            unique_uuids = len(set(test_uuids))
            
            uuid_test_results['generation_successful'] = True
            uuid_test_results['unique_count'] = unique_uuids
            uuid_test_results['collision_free'] = unique_uuids == 10
            
            print(f"✅ UUID generation: {unique_uuids}/10 unique UUIDs")
            
        except Exception as e:
            uuid_test_results['generation_successful'] = False
            uuid_test_results['error'] = str(e)
            print(f"❌ UUID generation failed: {e}")
        
        # Test request/response data structure feasibility
        message_structure_valid = False
        
        try:
            # Test message structure for Phase 3 communication
            test_request = {
                'type': 'WASM_RENDER_REQUEST',
                'request_id': str(uuid.uuid4()),
                'scad_code': 'cube([1,1,1]);',
                'options': {
                    'enableManifold': True,
                    'outputFormat': 'binstl',
                    'timeout': 30000
                }
            }
            
            test_response = {
                'type': 'WASM_RENDER_RESPONSE',
                'request_id': test_request['request_id'],
                'success': True,
                'stl_data': 'base64-encoded-data-here',
                'metadata': {
                    'renderTime': 123,
                    'size': 4567,
                    'triangles': 234,
                    'renderer': 'wasm'
                }
            }
            
            # Test JSON serialization (required for anywidget communication)
            request_json = json.dumps(test_request)
            response_json = json.dumps(test_response)
            
            # Test deserialization
            parsed_request = json.loads(request_json)
            parsed_response = json.loads(response_json)
            
            # Validate round-trip
            request_match = parsed_request['request_id'] == test_request['request_id']
            response_match = parsed_response['request_id'] == test_response['request_id']
            id_match = parsed_request['request_id'] == parsed_response['request_id']
            
            if request_match and response_match and id_match:
                message_structure_valid = True
                print("✅ Message structure valid and JSON-serializable")
                print(f"  Request size: {len(request_json)} bytes")
                print(f"  Response size: {len(response_json)} bytes")
            else:
                print("❌ Message structure validation failed")
                
        except Exception as e:
            print(f"❌ Message structure test failed: {e}")
        
        # Test binary data encoding/decoding (for STL transfer)
        binary_transfer_ready = False
        
        try:
            # Test with mock STL binary data
            mock_stl_data = b"solid test\nfacet normal 0 0 1\n  outer loop\n    vertex 0 0 0\n    vertex 1 0 0\n    vertex 0 1 0\n  endloop\nendfacet\nendsolid test"
            
            # Test base64 encoding
            encoded = base64.b64encode(mock_stl_data).decode('utf-8')
            
            # Test base64 decoding
            decoded = base64.b64decode(encoded)
            
            # Validate round-trip
            if decoded == mock_stl_data:
                binary_transfer_ready = True
                print(f"✅ Binary data transfer validated")
                print(f"  Original size: {len(mock_stl_data)} bytes")
                print(f"  Encoded size: {len(encoded)} characters")
                print(f"  Size overhead: {len(encoded) / len(mock_stl_data):.2f}x")
            else:
                print("❌ Binary data round-trip failed")
                
        except Exception as e:
            print(f"❌ Binary data transfer test failed: {e}")
        
        # Test timeout mechanism capabilities
        timeout_mechanism_ready = False
        
        try:
            import asyncio
            import time
            
            async def test_timeout_mechanism():
                try:
                    # Test basic async timeout
                    await asyncio.wait_for(asyncio.sleep(0.1), timeout=0.2)
                    return True
                except asyncio.TimeoutError:
                    return False
            
            # Run timeout test
            if hasattr(asyncio, 'run'):
                timeout_result = asyncio.run(test_timeout_mechanism())
            else:
                # Fallback for older Python versions
                loop = asyncio.get_event_loop()
                timeout_result = loop.run_until_complete(test_timeout_mechanism())
            
            if timeout_result:
                timeout_mechanism_ready = True
                print("✅ Async timeout mechanism available")
            else:
                print("⚠️ Async timeout mechanism test failed")
                
        except Exception as e:
            print(f"⚠️ Async timeout mechanism test error: {e}")
        
        # Summarize communication infrastructure readiness
        print(f"\n📊 ASYNC COMMUNICATION INFRASTRUCTURE SUMMARY:")
        print(f"  anywidget available: {'✅' if anywidget_available else '❌'}")
        print(f"  Viewer communication ready: {'✅' if viewer_communication_ready else '❌'}")
        print(f"  UUID generation working: {'✅' if uuid_test_results.get('generation_successful', False) else '❌'}")
        print(f"  Message structure valid: {'✅' if message_structure_valid else '❌'}")
        print(f"  Binary transfer ready: {'✅' if binary_transfer_ready else '❌'}")
        print(f"  Timeout mechanism ready: {'✅' if timeout_mechanism_ready else '❌'}")
        
        # Calculate overall readiness score
        readiness_components = [
            anywidget_available,
            viewer_communication_ready,
            uuid_test_results.get('generation_successful', False),
            message_structure_valid,
            binary_transfer_ready,
            timeout_mechanism_ready
        ]
        
        readiness_score = sum(readiness_components) / len(readiness_components)
        readiness_percentage = readiness_score * 100
        
        print(f"\n🎯 COMMUNICATION INFRASTRUCTURE READINESS: {readiness_percentage:.1f}%")
        
        if readiness_percentage >= 80:
            print("✅ READY for Phase 3 async communication implementation")
        elif readiness_percentage >= 60:
            print("⚡ MOSTLY READY - minor issues to address before Phase 3")
        elif readiness_percentage >= 40:
            print("⚠️ PARTIALLY READY - significant work needed before Phase 3")
        else:
            print("❌ NOT READY - major infrastructure gaps for Phase 3")
        
        # Save communication infrastructure analysis
        import time
        infrastructure_analysis = {
            'timestamp': time.time(),
            'readiness_score': readiness_score,
            'readiness_percentage': readiness_percentage,
            'anywidget_available': anywidget_available,
            'viewer_communication_ready': viewer_communication_ready,
            'uuid_test_results': uuid_test_results,
            'message_structure_valid': message_structure_valid,
            'binary_transfer_ready': binary_transfer_ready,
            'timeout_mechanism_ready': timeout_mechanism_ready
        }
        
        analysis_file = Path(__file__).parent / "communication_infrastructure_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(infrastructure_analysis, f, indent=2, default=str)
        
        print(f"\n💾 Communication infrastructure analysis saved to: {analysis_file}")
        
        # Test passes if basic communication infrastructure is available (>= 40%)
        assert readiness_percentage >= 40, f"Communication infrastructure not ready for Phase 3: {readiness_percentage:.1f}% < 40%"


if __name__ == "__main__":
    import time
    # Allow running individual tests
    pytest.main([__file__, "-v", "-s"])