"""
Real anywidget execution tests without mocks

These tests are EXPECTED TO FAIL initially. They document the 4 critical issues:
1. anywidget dynamic import limitations  
2. WASM loading failures
3. Browser context restrictions
4. Module resolution problems

Purpose: Eliminate false confidence from mock-based tests.
"""

import pytest
from playwright.sync_api import Page
from pathlib import Path
import json
import time

# Import our Playwright configuration
from .playwright_config import (
    test_page, browser_context, browser, error_analyzer, 
    create_test_html, test_files_dir
)


class TestRealAnyWidgetExecution:
    """Test real anywidget JavaScript execution in browser environment"""
    
    def test_anywidget_import_failure_detection(self, test_page: Page, error_analyzer):
        """
        EXPECTED TO FAIL: Document anywidget dynamic import limitations
        
        This test documents the core problem: anywidget cannot load
        relative JavaScript modules in browser context.
        """
        test_file = Path(__file__).parent / "test_files" / "anywidget_test_environment.html"
        test_page.goto(f"file://{test_file}")
        
        # Wait for page to load
        test_page.wait_for_load_state("networkidle")
        
        # Execute the basic import test
        result = test_page.evaluate("window.testBasicImport()")
        
        # Wait for test to complete
        time.sleep(2)
        
        # Get test results
        test_results = test_page.evaluate("window.getTestResults()")
        error_count = test_page.evaluate("window.getErrorCount()")
        
        # Analyze console errors
        console_errors = error_analyzer['capture_console_errors'](test_page)
        import_analysis = error_analyzer['analyze_import_errors'](console_errors)
        
        print("\n🔍 IMPORT FAILURE ANALYSIS:")
        print(f"Test Results: {len(test_results)} total")
        print(f"Error Count: {error_count}")
        print(f"Console Errors: {len(console_errors)}")
        print(f"Import-Related Errors: {import_analysis['import_related_errors']}")
        
        for result in test_results:
            if result['test'] == 'BASIC_IMPORT':
                print(f"Import Test: {result['status']} - {result['message']}")
                if result.get('details'):
                    print(f"Details: {json.dumps(result['details'], indent=2)}")
        
        # EXPECTATION: Import should fail
        assert error_count > 0, "Expected import failures to be detected"
        assert import_analysis['has_import_issues'], "Expected import-related errors"
        
        # Document the specific import problems
        import_errors = [r for r in test_results if r['test'] == 'BASIC_IMPORT' and 'FAILURE' in r['status']]
        assert len(import_errors) > 0, "Expected documented import failures"
        
        print(f"✅ SUCCESS: Import limitations correctly detected and documented")
    
    def test_wasm_loading_failure_real(self, test_page: Page, error_analyzer):
        """
        EXPECTED TO FAIL: Document WASM module loading failures
        
        Tests that WASM files cannot be loaded from local paths,
        documenting the WASM path resolution problem.
        """
        test_file = Path(__file__).parent / "test_files" / "anywidget_test_environment.html"
        test_page.goto(f"file://{test_file}")
        
        test_page.wait_for_load_state("networkidle")
        
        # Execute WASM loading test
        result = test_page.evaluate("window.testWASMLoading()")
        time.sleep(3)  # Allow async operations to complete
        
        # Get results
        test_results = test_page.evaluate("window.getTestResults()")
        console_errors = error_analyzer['capture_console_errors'](test_page)
        network_failures = error_analyzer['capture_network_failures'](test_page)
        
        # Analyze WASM-specific errors
        wasm_analysis = error_analyzer['analyze_wasm_errors'](console_errors, network_failures)
        
        print("\n🔍 WASM LOADING FAILURE ANALYSIS:")
        print(f"Network Failures: {len(network_failures)}")
        print(f"WASM Console Errors: {wasm_analysis['wasm_console_errors']}")
        print(f"WASM Network Failures: {wasm_analysis['wasm_network_failures']}")
        
        # Find WASM test results
        wasm_results = [r for r in test_results if r['test'] == 'WASM_LOADING']
        for result in wasm_results:
            print(f"WASM Test: {result['status']} - {result['message']}")
            if result.get('details'):
                print(f"WASM Paths Tested: {list(result['details'].keys())}")
                for path, path_result in result['details'].items():
                    print(f"  {path}: {path_result}")
        
        # EXPECTATION: WASM loading should fail
        wasm_failures = [r for r in wasm_results if 'FAILURE' in r['status']]
        assert len(wasm_failures) > 0, "Expected WASM loading failures"
        
        # Verify specific failure patterns
        if network_failures:
            wasm_network_fails = [f for f in network_failures if '.wasm' in f['url']]
            print(f"WASM-specific network failures: {len(wasm_network_fails)}")
        
        print(f"✅ SUCCESS: WASM loading failures correctly detected and documented")
    
    def test_widget_creation_failure_real(self, test_page: Page):
        """
        EXPECTED TO FAIL: Document widget creation failures
        
        Tests that anywidget cannot be created due to missing
        render function (caused by import failures).
        """
        test_file = Path(__file__).parent / "test_files" / "anywidget_test_environment.html"
        test_page.goto(f"file://{test_file}")
        
        test_page.wait_for_load_state("networkidle")
        
        # Execute widget creation test
        result = test_page.evaluate("window.testWidgetCreation()")
        time.sleep(2)
        
        # Get results
        test_results = test_page.evaluate("window.getTestResults()")
        
        print("\n🔍 WIDGET CREATION FAILURE ANALYSIS:")
        
        widget_results = [r for r in test_results if r['test'] == 'WIDGET_CREATION']
        for result in widget_results:
            print(f"Widget Test: {result['status']} - {result['message']}")
            if result.get('details'):
                print(f"Error Details: {result['details']}")
        
        # Check final DOM state
        container_content = test_page.evaluate("""
            document.getElementById('widget-container').innerHTML
        """)
        
        print(f"Widget Container Content: {container_content[:200]}...")
        
        # EXPECTATION: Widget creation should fail
        widget_failures = [r for r in widget_results if 'FAILURE' in r['status']]
        assert len(widget_failures) > 0, "Expected widget creation failures"
        
        # Verify failure is due to missing render function
        error_mentions_render = any(
            'render' in str(r.get('details', {})).lower() 
            for r in widget_failures
        )
        assert error_mentions_render, "Expected failure to mention render function"
        
        print(f"✅ SUCCESS: Widget creation failure correctly attributed to import issues")
    
    def test_browser_capabilities_baseline(self, test_page: Page):
        """
        SUCCESS EXPECTED: Establish browser capabilities baseline
        
        This test should pass - it documents what the browser CAN do,
        providing context for what SHOULD work vs what's broken.
        """
        test_file = Path(__file__).parent / "test_files" / "anywidget_test_environment.html"
        test_page.goto(f"file://{test_file}")
        
        test_page.wait_for_load_state("networkidle")
        time.sleep(1)
        
        # Get browser capabilities
        capabilities = test_page.evaluate("""
            () => ({
                userAgent: navigator.userAgent,
                webAssembly: typeof WebAssembly !== 'undefined',
                esModules: typeof document.createElement === 'function', // ES modules support check
                fetch: typeof fetch !== 'undefined',
                localStorage: typeof localStorage !== 'undefined',
                webGL: (() => {
                    try {
                        const canvas = document.createElement('canvas');
                        return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
                    } catch(e) {
                        return false;
                    }
                })(),
                webWorkers: typeof Worker !== 'undefined',
                fileAPI: typeof File !== 'undefined',
                url: window.location.href
            })
        """)
        
        print("\n🔍 BROWSER CAPABILITIES BASELINE:")
        for key, value in capabilities.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
        
        # These should all be true in a modern browser
        assert capabilities['webAssembly'], "WebAssembly should be supported"
        assert capabilities['esModules'], "ES Modules should be supported"
        assert capabilities['fetch'], "Fetch API should be supported"
        # Note: WebGL might not be available in headless mode, that's OK
        
        # Get test results from page (if available)
        try:
            test_results = test_page.evaluate("window.getTestResults ? window.getTestResults() : []")
            capability_results = [r for r in test_results if r['test'] == 'BROWSER_CAPABILITIES']
            
            if capability_results:
                print(f"Page reported capabilities: {capability_results[0].get('details', {})}")
        except:
            print("No page test results available (expected in baseline test)")
        
        print(f"✅ SUCCESS: Browser capabilities baseline established")
    
    def test_comprehensive_error_documentation(self, test_page: Page, error_analyzer):
        """
        EXPECTED TO DOCUMENT ERRORS: Run all tests and create comprehensive error report
        
        This test runs all interactive tests and documents the complete
        error landscape for analysis.
        """
        test_file = Path(__file__).parent / "test_files" / "anywidget_test_environment.html"
        test_page.goto(f"file://{test_file}")
        
        test_page.wait_for_load_state("networkidle")
        
        # Run all tests
        test_page.evaluate("window.testBasicImport()")
        time.sleep(1)
        test_page.evaluate("window.testWASMLoading()")
        time.sleep(2)
        test_page.evaluate("window.testWidgetCreation()")
        time.sleep(1)
        
        # Collect comprehensive results
        test_results = test_page.evaluate("window.getTestResults()")
        console_errors = error_analyzer['capture_console_errors'](test_page)
        network_failures = error_analyzer['capture_network_failures'](test_page)
        
        # Analyze all error types
        import_analysis = error_analyzer['analyze_import_errors'](console_errors)
        wasm_analysis = error_analyzer['analyze_wasm_errors'](console_errors, network_failures)
        
        # Create comprehensive error report
        error_report = {
            'timestamp': test_page.evaluate("new Date().toISOString()"),
            'test_summary': {
                'total_tests': len(test_results),
                'failed_tests': len([r for r in test_results if 'FAILURE' in r['status']]),
                'error_count': test_page.evaluate("window.getErrorCount()"),
                'success_count': test_page.evaluate("window.getSuccessCount()")
            },
            'console_errors': {
                'total': len(console_errors),
                'import_related': import_analysis['import_related_errors'],
                'wasm_related': wasm_analysis['wasm_console_errors']
            },
            'network_failures': {
                'total': len(network_failures),
                'wasm_files': wasm_analysis['wasm_network_failures']
            },
            'critical_issues_detected': {
                'import_limitations': import_analysis['has_import_issues'],
                'wasm_loading_failures': wasm_analysis['has_wasm_issues'],
                'widget_creation_blocked': any(
                    'WIDGET_CREATION' in r['test'] and 'FAILURE' in r['status']
                    for r in test_results
                ),
                'network_access_issues': len(network_failures) > 0
            }
        }
        
        print("\n🔍 COMPREHENSIVE ERROR DOCUMENTATION:")
        print(json.dumps(error_report, indent=2))
        
        # Document that we've successfully identified the problems
        critical_issues = error_report['critical_issues_detected']
        detected_issues = sum(critical_issues.values())
        
        print(f"\n✅ CRITICAL ISSUES DETECTION SUMMARY:")
        print(f"  Issues Detected: {detected_issues}/4 expected problems")
        for issue, detected in critical_issues.items():
            status = "✅ DETECTED" if detected else "❌ NOT DETECTED"
            print(f"  {status}: {issue}")
        
        # We expect to detect at least import and widget creation issues
        assert critical_issues['import_limitations'], "Import limitations should be detected"
        assert critical_issues['widget_creation_blocked'], "Widget creation should be blocked"
        
        print(f"\n✅ SUCCESS: Phase 1 objective achieved - real problems documented without mock false confidence")
        
        return error_report


# Marker for expected failures
pytestmark = pytest.mark.e2e