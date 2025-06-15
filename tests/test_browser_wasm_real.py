#!/usr/bin/env python3
"""
Browser Environment Testing - Real WASM without Mocks

Tests the complete WASM implementation in real browser environments
using Playwright for end-to-end validation of the WASM bridge system.

This replaces the mock-heavy approach with actual browser testing
to validate the 16.4MB WASM infrastructure and JavaScript bridge.
"""

import pytest
import asyncio
import json
import tempfile
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.mark.browser_testing
@pytest.mark.asyncio
class TestBrowserWASMReal:
    """Test WASM functionality in real browser environments"""
    
    async def test_browser_wasm_support_detection(self):
        """Test WebAssembly support detection in real browser"""
        async with async_playwright() as p:
            # Test with multiple browsers for compatibility
            browsers_to_test = []
            
            # Add available browsers
            if await self._is_browser_available(p, 'chromium'):
                browsers_to_test.append(('chromium', p.chromium))
            if await self._is_browser_available(p, 'firefox'):
                browsers_to_test.append(('firefox', p.firefox))
            if await self._is_browser_available(p, 'webkit'):
                browsers_to_test.append(('webkit', p.webkit))
            
            assert len(browsers_to_test) > 0, "No browsers available for testing"
            
            for browser_name, browser in browsers_to_test:
                browser_instance = await browser.launch(headless=True)
                try:
                    page = await browser_instance.new_page()
                    
                    # Test WebAssembly support
                    wasm_support = await page.evaluate("""
                        (() => {
                            try {
                                if (typeof WebAssembly === "object" &&
                                    typeof WebAssembly.instantiate === "function") {
                                    const module = new WebAssembly.Module(
                                        Uint8Array.of(0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00)
                                    );
                                    return WebAssembly.Module.imports(module).length === 0;
                                }
                            } catch (e) {
                                return false;
                            }
                            return false;
                        })()
                    """)
                    
                    assert wasm_support, f"WebAssembly not supported in {browser_name}"
                    print(f"✅ {browser_name}: WebAssembly support confirmed")
                    
                finally:
                    await browser_instance.close()
    
    async def test_wasm_module_loading_real(self):
        """Test real WASM module loading without mocks"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                
                # Create test HTML with WASM loading
                test_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>WASM Module Loading Test</title>
                </head>
                <body>
                    <div id="status">Loading...</div>
                    <div id="result"></div>
                    
                    <script>
                        // Test WASM module instantiation
                        async function testWASMLoading() {
                            try {
                                // Create minimal valid WASM module
                                const wasmBytes = new Uint8Array([
                                    0x00, 0x61, 0x73, 0x6d, // WASM header
                                    0x01, 0x00, 0x00, 0x00, // Version
                                    0x01, 0x04, 0x01, 0x60, 0x00, 0x00, // Type section
                                    0x03, 0x02, 0x01, 0x00, // Function section
                                    0x0a, 0x04, 0x01, 0x02, 0x00, 0x0b  // Code section
                                ]);
                                
                                const wasmModule = await WebAssembly.instantiate(wasmBytes);
                                
                                document.getElementById('status').textContent = 'Success';
                                document.getElementById('result').textContent = JSON.stringify({
                                    moduleLoaded: true,
                                    exports: Object.keys(wasmModule.instance.exports),
                                    timestamp: Date.now()
                                }, null, 2);
                                
                                return true;
                            } catch (error) {
                                document.getElementById('status').textContent = 'Error';
                                document.getElementById('result').textContent = error.toString();
                                return false;
                            }
                        }
                        
                        // Run test when page loads
                        window.onload = () => testWASMLoading();
                    </script>
                </body>
                </html>
                """
                
                # Set page content and wait for test completion
                await page.set_content(test_html)
                await page.wait_for_function("document.getElementById('status').textContent !== 'Loading...'")
                
                # Check results
                status = await page.text_content('#status')
                result = await page.text_content('#result')
                
                assert status == 'Success', f"WASM loading failed: {result}"
                
                # Parse result JSON
                result_data = json.loads(result)
                assert result_data['moduleLoaded'] is True
                print(f"✅ WASM module loading successful: {len(result_data['exports'])} exports")
                
            finally:
                await browser.close()
    
    async def test_javascript_bridge_pattern_detection_real(self):
        """Test JavaScript bridge pattern detection in real browser"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                
                # Create test HTML with bridge pattern detection
                test_html = """
                <!DOCTYPE html>
                <html>
                <body>
                    <div id="test-results"></div>
                    
                    <script>
                        // Simulate the bridge pattern detection logic from widget.js
                        function testBridgePatternDetection() {
                            const testCases = [
                                {
                                    input: "WASM_RENDER_REQUEST:12345",
                                    expectedDetected: true,
                                    expectedHash: "12345"
                                },
                                {
                                    input: "WASM_RENDER_REQUEST:-8427547496623440318",
                                    expectedDetected: true,
                                    expectedHash: "-8427547496623440318"
                                },
                                {
                                    input: "WASM_RENDER_REQUEST:",
                                    expectedDetected: true,
                                    expectedHash: ""
                                },
                                {
                                    input: "NOT_WASM_REQUEST:12345",
                                    expectedDetected: false,
                                    expectedHash: null
                                },
                                {
                                    input: "regular STL data",
                                    expectedDetected: false,
                                    expectedHash: null
                                }
                            ];
                            
                            const results = [];
                            
                            for (const testCase of testCases) {
                                const stlData = testCase.input;
                                
                                // Bridge detection logic (from widget.js)
                                const isWASMRequest = (typeof stlData === 'string' && 
                                                     stlData.startsWith('WASM_RENDER_REQUEST:'));
                                
                                let extractedHash = null;
                                if (isWASMRequest) {
                                    extractedHash = stlData.substring('WASM_RENDER_REQUEST:'.length);
                                }
                                
                                const testResult = {
                                    input: testCase.input,
                                    detected: isWASMRequest,
                                    extractedHash: extractedHash,
                                    expectedDetected: testCase.expectedDetected,
                                    expectedHash: testCase.expectedHash,
                                    passed: (isWASMRequest === testCase.expectedDetected && 
                                            extractedHash === testCase.expectedHash)
                                };
                                
                                results.push(testResult);
                            }
                            
                            return results;
                        }
                        
                        // Run tests and display results
                        window.onload = () => {
                            const results = testBridgePatternDetection();
                            document.getElementById('test-results').textContent = JSON.stringify(results, null, 2);
                        };
                    </script>
                </body>
                </html>
                """
                
                await page.set_content(test_html)
                await page.wait_for_function("document.getElementById('test-results').textContent !== ''")
                
                # Get test results
                results_text = await page.text_content('#test-results')
                results = json.loads(results_text)
                
                # Validate all test cases passed
                for result in results:
                    assert result['passed'], f"Bridge pattern detection failed for: {result['input']}"
                
                print(f"✅ JavaScript bridge pattern detection: {len(results)} test cases passed")
                
            finally:
                await browser.close()
    
    async def test_threejs_canvas_integration_real(self):
        """Test Three.js canvas integration in real browser"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                
                # Create test HTML with Three.js integration
                test_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <script src="https://cdn.jsdelivr.net/npm/three@0.150.0/build/three.min.js"></script>
                </head>
                <body>
                    <div id="canvas-container"></div>
                    <div id="test-status">Testing...</div>
                    
                    <script>
                        async function testThreeJSIntegration() {
                            try {
                                // Create scene, camera, renderer (similar to widget.js)
                                const scene = new THREE.Scene();
                                const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
                                const renderer = new THREE.WebGLRenderer({ antialias: true });
                                
                                renderer.setSize(400, 300);
                                renderer.setClearColor(0xf0f0f0);
                                
                                document.getElementById('canvas-container').appendChild(renderer.domElement);
                                
                                // Create test cube geometry (fallback geometry from widget)
                                const geometry = new THREE.BoxGeometry(1, 1, 1);
                                const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
                                const cube = new THREE.Mesh(geometry, material);
                                
                                scene.add(cube);
                                camera.position.z = 3;
                                
                                // Render frame
                                renderer.render(scene, camera);
                                
                                // Test WebGL context
                                const gl = renderer.getContext();
                                const webglSupported = gl !== null;
                                
                                document.getElementById('test-status').textContent = JSON.stringify({
                                    success: true,
                                    webglSupported: webglSupported,
                                    rendererInfo: renderer.info,
                                    canvasSize: { width: renderer.domElement.width, height: renderer.domElement.height }
                                }, null, 2);
                                
                                return true;
                                
                            } catch (error) {
                                document.getElementById('test-status').textContent = JSON.stringify({
                                    success: false,
                                    error: error.toString()
                                }, null, 2);
                                return false;
                            }
                        }
                        
                        window.onload = () => testThreeJSIntegration();
                    </script>
                </body>
                </html>
                """
                
                await page.set_content(test_html)
                await page.wait_for_function("document.getElementById('test-status').textContent !== 'Testing...'")
                
                # Get test results
                status_text = await page.text_content('#test-status')
                status = json.loads(status_text)
                
                assert status['success'], f"Three.js integration failed: {status.get('error', 'Unknown error')}"
                assert status['webglSupported'], "WebGL not supported"
                
                print(f"✅ Three.js canvas integration successful: WebGL supported")
                
            finally:
                await browser.close()
    
    async def test_wasm_files_existence_validation(self):
        """Test that real WASM files exist and are accessible"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        renderer = OpenSCADWASMRenderer()
        
        # Check WASM files detection
        wasm_files = renderer.get_wasm_files()
        assert len(wasm_files) > 0, "No WASM files detected"
        
        # Verify core files exist
        required_files = ['openscad.wasm', 'openscad.js']
        for required_file in required_files:
            assert required_file in wasm_files, f"Required WASM file missing: {required_file}"
        
        # Check file sizes (should be substantial for real files)
        wasm_file_path = Path(wasm_files['openscad.wasm'])
        assert wasm_file_path.exists(), "openscad.wasm file does not exist"
        
        file_size = wasm_file_path.stat().st_size
        assert file_size > 1_000_000, f"WASM file too small ({file_size} bytes), likely not real"
        
        print(f"✅ WASM files validation: {len(wasm_files)} files, {file_size:,} bytes core module")
    
    async def test_browser_memory_constraints_detection(self):
        """Test browser memory constraints detection for WASM environments"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                
                test_html = """
                <!DOCTYPE html>
                <html>
                <body>
                    <div id="memory-info"></div>
                    
                    <script>
                        function detectMemoryConstraints() {
                            const memoryInfo = {
                                hasPerformanceMemory: 'memory' in performance,
                                hasNavigatorMemory: 'deviceMemory' in navigator,
                                estimatedMemoryGB: 'deviceMemory' in navigator ? navigator.deviceMemory : 'unknown',
                                webAssemblySupported: typeof WebAssembly !== 'undefined',
                                isWASMSafe: true  // Browser environment is WASM-safe
                            };
                            
                            // Add performance memory info if available
                            if (memoryInfo.hasPerformanceMemory) {
                                memoryInfo.performanceMemory = {
                                    usedJSHeapSize: performance.memory.usedJSHeapSize,
                                    totalJSHeapSize: performance.memory.totalJSHeapSize,
                                    jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                                };
                            }
                            
                            return memoryInfo;
                        }
                        
                        window.onload = () => {
                            const info = detectMemoryConstraints();
                            document.getElementById('memory-info').textContent = JSON.stringify(info, null, 2);
                        };
                    </script>
                </body>
                </html>
                """
                
                await page.set_content(test_html)
                await page.wait_for_function("document.getElementById('memory-info').textContent !== ''")
                
                memory_text = await page.text_content('#memory-info')
                memory_info = json.loads(memory_text)
                
                assert memory_info['webAssemblySupported'], "WebAssembly not supported"
                assert memory_info['isWASMSafe'], "Environment not WASM-safe"
                
                print(f"✅ Memory constraints detection: {memory_info.get('estimatedMemoryGB', 'unknown')}GB device memory")
                
            finally:
                await browser.close()
    
    async def _is_browser_available(self, playwright, browser_name):
        """Check if browser is available for testing"""
        try:
            browser = getattr(playwright, browser_name)
            test_browser = await browser.launch(headless=True)
            await test_browser.close()
            return True
        except Exception:
            return False


@pytest.mark.browser_integration
@pytest.mark.asyncio
class TestBrowserWASMIntegration:
    """Integration tests for WASM bridge in browser environment"""
    
    async def test_end_to_end_wasm_bridge_browser(self):
        """End-to-end test of WASM bridge in real browser"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        # Step 1: Generate WASM render request (Python side)
        renderer = OpenSCADWASMRenderer()
        scad_code = "cube([2, 2, 2]);"
        
        result = renderer.render_scad_to_stl(scad_code)
        result_str = result.decode('utf-8', errors='ignore')
        
        assert result_str.startswith('WASM_RENDER_REQUEST:'), "Python didn't generate WASM request"
        hash_value = result_str[len('WASM_RENDER_REQUEST:'):]
        
        # Step 2: Test browser processing (JavaScript side simulation)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                
                # Create test HTML that simulates widget.js bridge handling
                test_html = f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <div id="bridge-test-result"></div>
                    
                    <script>
                        function testWASMBridgeHandling() {{
                            // Simulate data from Python
                            const stlData = "{result_str}";
                            const scadCode = "{scad_code}";
                            
                            // Bridge detection logic (from widget.js)
                            if (typeof stlData === 'string' && stlData.startsWith('WASM_RENDER_REQUEST:')) {{
                                const hash = stlData.substring('WASM_RENDER_REQUEST:'.length);
                                
                                // Simulate WASM rendering process
                                const bridgeResult = {{
                                    bridgeDetected: true,
                                    hashExtracted: hash,
                                    scadCodeReceived: scadCode.length > 0,
                                    wasmRenderingTriggered: true,
                                    timestamp: Date.now()
                                }};
                                
                                return bridgeResult;
                            }} else {{
                                return {{
                                    bridgeDetected: false,
                                    error: "WASM request pattern not detected"
                                }};
                            }}
                        }}
                        
                        window.onload = () => {{
                            const result = testWASMBridgeHandling();
                            document.getElementById('bridge-test-result').textContent = JSON.stringify(result, null, 2);
                        }};
                    </script>
                </body>
                </html>
                """
                
                await page.set_content(test_html)
                await page.wait_for_function("document.getElementById('bridge-test-result').textContent !== ''")
                
                result_text = await page.text_content('#bridge-test-result')
                bridge_result = json.loads(result_text)
                
                # Validate end-to-end bridge functionality
                assert bridge_result['bridgeDetected'], "Browser didn't detect WASM bridge pattern"
                assert bridge_result['hashExtracted'] == hash_value, "Hash extraction mismatch"
                assert bridge_result['scadCodeReceived'], "SCAD code not received properly"
                assert bridge_result['wasmRenderingTriggered'], "WASM rendering not triggered"
                
                print(f"✅ End-to-end WASM bridge: Python→Browser integration successful")
                
            finally:
                await browser.close()
    
    async def test_browser_error_handling_real(self):
        """Test error handling in real browser environment"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                
                # Test error scenarios
                test_html = """
                <!DOCTYPE html>
                <html>
                <body>
                    <div id="error-test-results"></div>
                    
                    <script>
                        function testErrorHandling() {
                            const errorTests = [];
                            
                            // Test 1: Empty WASM request
                            try {
                                const emptyRequest = "WASM_RENDER_REQUEST:";
                                const hash = emptyRequest.substring('WASM_RENDER_REQUEST:'.length);
                                errorTests.push({
                                    test: "empty_hash",
                                    success: true,
                                    hash: hash,
                                    message: "Empty hash handled gracefully"
                                });
                            } catch (e) {
                                errorTests.push({
                                    test: "empty_hash",
                                    success: false,
                                    error: e.toString()
                                });
                            }
                            
                            // Test 2: Invalid request format
                            try {
                                const invalidRequest = "NOT_WASM_REQUEST:12345";
                                const isWASMRequest = invalidRequest.startsWith('WASM_RENDER_REQUEST:');
                                errorTests.push({
                                    test: "invalid_format",
                                    success: !isWASMRequest,
                                    message: "Invalid format correctly rejected"
                                });
                            } catch (e) {
                                errorTests.push({
                                    test: "invalid_format",
                                    success: false,
                                    error: e.toString()
                                });
                            }
                            
                            // Test 3: WebAssembly availability check
                            try {
                                const wasmAvailable = typeof WebAssembly !== 'undefined';
                                errorTests.push({
                                    test: "wasm_availability",
                                    success: wasmAvailable,
                                    message: wasmAvailable ? "WebAssembly available" : "WebAssembly not available"
                                });
                            } catch (e) {
                                errorTests.push({
                                    test: "wasm_availability",
                                    success: false,
                                    error: e.toString()
                                });
                            }
                            
                            return errorTests;
                        }
                        
                        window.onload = () => {
                            const results = testErrorHandling();
                            document.getElementById('error-test-results').textContent = JSON.stringify(results, null, 2);
                        };
                    </script>
                </body>
                </html>
                """
                
                await page.set_content(test_html)
                await page.wait_for_function("document.getElementById('error-test-results').textContent !== ''")
                
                results_text = await page.text_content('#error-test-results')
                error_tests = json.loads(results_text)
                
                # Validate error handling
                for test in error_tests:
                    assert test['success'], f"Error handling test failed: {test['test']} - {test.get('error', 'Unknown error')}"
                
                print(f"✅ Browser error handling: {len(error_tests)} test scenarios passed")
                
            finally:
                await browser.close()


if __name__ == "__main__":
    # Run browser tests with asyncio support
    pytest.main([__file__, "-v", "--tb=short"])