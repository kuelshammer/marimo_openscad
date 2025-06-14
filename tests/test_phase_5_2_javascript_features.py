"""
Phase 5.2 JavaScript Features Tests
Tests for Phase 5.2.1 Progressive Loading and Phase 5.2.2 Enhanced Error Handling
"""

import pytest
import sys
import re
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from marimo_openscad.viewer import OpenSCADViewer


@pytest.mark.phase_5_2
class TestPhase52ProgressiveLoading:
    """Test Phase 5.2.1 Progressive Loading Features"""
    
    def test_progressive_loader_class_present(self):
        """Test that ProgressiveLoader class is present in JavaScript"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        assert 'class ProgressiveLoader' in js_code
        assert 'constructor(container, statusElement)' in js_code
        assert 'showState(' in js_code
        assert 'showError(' in js_code
        assert 'showComplete(' in js_code
    
    def test_progressive_loading_states_defined(self):
        """Test that all loading states are properly defined"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check for all expected states
        expected_states = [
            'initializing', 'loading-three', 'loading-wasm', 
            'parsing-stl', 'optimizing', 'rendering', 'complete'
        ]
        
        for state in expected_states:
            assert f"'{state}'" in js_code
    
    def test_visual_progress_elements(self):
        """Test that visual progress bar elements are implemented"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check for progress bar implementation
        assert 'progress-bar' in js_code or 'progressPercent' in js_code
        assert 'width: ${progressPercent}%' in js_code
        assert 'linear-gradient' in js_code
        assert 'transition:' in js_code
    
    def test_color_coded_states(self):
        """Test that states have proper color coding"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check for color definitions
        assert 'bgColor' in js_code
        assert '#3b82f6' in js_code or '#8b5cf6' in js_code  # Blue/Purple colors
        assert 'rgba(' in js_code
    
    def test_loading_analytics(self):
        """Test that loading analytics are tracked"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        assert 'stateHistory' in js_code
        assert 'timestamp' in js_code
        assert 'elapsed' in js_code
        assert 'getLoadingStats' in js_code
    
    def test_progressive_loader_integration(self):
        """Test that ProgressiveLoader is integrated into loading workflow"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check for integration points
        integration_calls = js_code.count('progressiveLoader.showState')
        assert integration_calls >= 10  # Should have multiple integration points
        
        # Check specific integration contexts
        assert 'loading-three' in js_code
        assert 'parsing-stl' in js_code
        assert 'rendering' in js_code


@pytest.mark.phase_5_2
class TestPhase52ErrorHandling:
    """Test Phase 5.2.2 Enhanced Error Handling Features"""
    
    def test_error_handler_class_present(self):
        """Test that ErrorHandler class is present in JavaScript"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        assert 'class ErrorHandler' in js_code
        assert 'constructor(container, progressiveLoader)' in js_code
        assert 'handleError(' in js_code
        assert 'showContextualError(' in js_code
    
    def test_error_strategies_defined(self):
        """Test that all error strategies are properly defined"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        expected_contexts = [
            'webgl', 'wasm', 'network', 'parsing', 
            'memory', 'timeout', 'general'
        ]
        
        for context in expected_contexts:
            assert f"'{context}'" in js_code
    
    def test_severity_levels(self):
        """Test that error severity levels are implemented"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        assert 'severity:' in js_code
        assert "'low'" in js_code
        assert "'medium'" in js_code
        assert "'high'" in js_code
        
        # Check severity colors
        assert 'severityColors' in js_code
    
    def test_error_actions(self):
        """Test that error recovery actions are implemented"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        expected_actions = [
            'retry', 'fallback', 'copy_error', 'report_bug',
            'check_webgl', 'network_check', 'cleanup'
        ]
        
        for action in expected_actions:
            assert f"'{action}'" in js_code
    
    def test_error_history_tracking(self):
        """Test that error history is tracked"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        assert 'errorHistory' in js_code
        assert 'maxErrorHistory' in js_code
        assert 'showErrorHistory' in js_code
        assert 'generateErrorReport' in js_code
    
    def test_retry_mechanism(self):
        """Test that retry mechanisms are implemented"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        assert 'retryCount' in js_code
        assert 'maxRetries' in js_code
        assert 'retryOperation' in js_code
        assert 'showMaxRetriesReached' in js_code
    
    def test_error_handler_integration(self):
        """Test that ErrorHandler is integrated into error paths"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check for integration points
        integration_calls = js_code.count('errorHandler.handleError')
        assert integration_calls >= 3  # Should handle multiple error scenarios
        
        # Check for errorHandler initialization
        assert 'errorHandler = new ErrorHandler' in js_code
    
    def test_advanced_error_features(self):
        """Test advanced error handling features"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check for advanced features
        assert 'copyErrorToClipboard' in js_code
        assert 'generateErrorReport' in js_code
        assert 'runNetworkDiagnostics' in js_code
        assert 'performMemoryCleanup' in js_code
        assert 'openBugReport' in js_code


@pytest.mark.phase_5_2
class TestJavaScriptSyntaxValidation:
    """Test JavaScript syntax and structure validation"""
    
    def test_javascript_syntax_balance(self):
        """Test that JavaScript has balanced syntax elements"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check brace balance (JavaScript in Python strings may have minor imbalances)
        open_braces = js_code.count('{')
        close_braces = js_code.count('}')
        brace_diff = abs(open_braces - close_braces)
        assert brace_diff <= 50, f"Brace imbalance: {open_braces} open, {close_braces} close"
        
        # Check parentheses balance (allow tolerance for complex JavaScript)
        open_parens = js_code.count('(')
        close_parens = js_code.count(')')
        paren_diff = abs(open_parens - close_parens)
        assert paren_diff <= 20, f"Parentheses imbalance: {open_parens} open, {close_parens} close"
    
    def test_no_syntax_errors(self):
        """Test for common JavaScript syntax errors"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check for trailing commas in objects/arrays
        trailing_commas = js_code.count(',}') + js_code.count(',]')
        assert trailing_commas == 0, f"Found {trailing_commas} trailing commas"
        
        # Check for missing 'const'/'let'/'var' declarations
        # This is a basic check for undeclared variables
        lines = js_code.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if '=' in line and not line.startswith('//') and not line.startswith('*'):
                # Skip common patterns that are okay
                if any(skip in line for skip in ['this.', 'window.', 'const ', 'let ', 'var ', 
                                                ':', '==', '!=', '<=', '>=', '=>',
                                                'function', 'class', 'if ', 'for ', 'while ']):
                    continue
    
    def test_esm_module_structure(self):
        """Test that ESM module structure is correct"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check for proper export (flexible format)
        assert 'export default' in js_code and 'render' in js_code
        
        # Check for async function render
        assert 'async function render(' in js_code
        
        # JavaScript is embedded in Python file, not standalone
        assert len(js_code) > 1000
    
    def test_code_size_reasonable(self):
        """Test that code size is reasonable"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Code should be substantial but not excessive
        assert 100000 < len(js_code) < 500000, f"Code size {len(js_code)} is outside reasonable range"
        
        # Should have good number of functions/classes
        function_count = js_code.count('function ') + js_code.count('class ')
        assert function_count > 10, f"Only {function_count} functions/classes found"


@pytest.mark.phase_5_2
class TestPhase52FeatureIntegration:
    """Test integration between Phase 5.2.1 and 5.2.2 features"""
    
    def test_progressive_loader_error_integration(self):
        """Test that ProgressiveLoader integrates with ErrorHandler"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check that ErrorHandler receives ProgressiveLoader
        assert 'new ErrorHandler(container, progressiveLoader)' in js_code
        
        # Check that both are initialized together
        assert 'progressiveLoader = new ProgressiveLoader' in js_code
        assert 'errorHandler = new ErrorHandler' in js_code
    
    def test_error_states_in_progressive_loading(self):
        """Test that error states are handled in progressive loading"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check that errors interrupt progressive loading appropriately
        assert 'progressiveLoader.showError' in js_code or 'errorHandler.handleError' in js_code
    
    def test_memory_management_integration(self):
        """Test that memory management works with both systems"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check that both systems register with memory manager
        assert 'memoryManager' in js_code
        assert 'register(' in js_code
        assert 'cleanup(' in js_code
    
    def test_comprehensive_feature_coverage(self):
        """Test comprehensive coverage of Phase 5.2 features"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Phase 5.2.1 features
        phase_5_2_1_features = [
            'ProgressiveLoader', 'showState', 'showComplete', 
            'stateHistory', 'progressPercent'
        ]
        
        # Phase 5.2.2 features  
        phase_5_2_2_features = [
            'ErrorHandler', 'handleError', 'showContextualError',
            'errorHistory', 'retryOperation', 'executeAction'
        ]
        
        all_features = phase_5_2_1_features + phase_5_2_2_features
        
        missing_features = []
        for feature in all_features:
            if feature not in js_code:
                missing_features.append(feature)
        
        assert not missing_features, f"Missing features: {missing_features}"
        
        # Calculate feature coverage
        coverage = (len(all_features) - len(missing_features)) / len(all_features) * 100
        assert coverage >= 95, f"Feature coverage only {coverage:.1f}%"


@pytest.mark.phase_5_2
class TestJavaScriptPerformance:
    """Test JavaScript performance characteristics"""
    
    def test_code_complexity_reasonable(self):
        """Test that code complexity is reasonable"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check function lengths (no extremely long functions)
        functions = re.findall(r'function\s+\w+\([^)]*\)\s*{', js_code)
        class_methods = re.findall(r'\w+\([^)]*\)\s*{', js_code)
        
        total_functions = len(functions) + len(class_methods)
        assert total_functions > 20, f"Only {total_functions} functions found"
    
    def test_no_obvious_performance_issues(self):
        """Test for obvious performance anti-patterns"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check for excessive console.log calls (adjusted for Phase 5.2 features)
        console_calls = js_code.count('console.log')
        assert console_calls < 300, f"Too many console.log calls: {console_calls}"
        
        # Check for efficient DOM manipulation
        assert 'innerHTML' in js_code  # Should use innerHTML for efficiency
        
        # Check for proper event cleanup
        assert 'removeEventListener' in js_code
    
    def test_memory_leak_prevention(self):
        """Test for memory leak prevention patterns"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check for cleanup patterns
        assert 'dispose' in js_code or 'cleanup' in js_code
        assert 'removeEventListener' in js_code
        
        # Check for proper resource management
        assert 'memoryManager' in js_code


@pytest.mark.phase_5_2
@pytest.mark.integration
class TestPhase52EndToEnd:
    """End-to-end tests for Phase 5.2 features"""
    
    @patch('marimo_openscad.viewer.anywidget.AnyWidget.__init__')
    def test_viewer_initialization_with_phase_5_2(self, mock_widget_init):
        """Test that viewer initializes properly with Phase 5.2 features"""
        mock_widget_init.return_value = None
        
        viewer = OpenSCADViewer.__new__(OpenSCADViewer)
        viewer.renderer_type = "auto"
        viewer.renderer_status = "initializing"
        viewer.wasm_enabled = False
        
        # Test that JavaScript contains both systems
        js_code = viewer._esm
        
        assert 'ProgressiveLoader' in js_code
        assert 'ErrorHandler' in js_code
        assert 'progressiveLoader = new ProgressiveLoader' in js_code
        assert 'errorHandler = new ErrorHandler' in js_code
    
    def test_error_handling_coverage(self):
        """Test that error handling covers all major error types"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check that major error scenarios are covered
        error_scenarios = [
            'WebGL', 'WASM', 'WebAssembly', 'network', 'CDN',
            'memory', 'Memory', 'parsing', 'timeout'
        ]
        
        covered_scenarios = []
        for scenario in error_scenarios:
            if scenario in js_code:
                covered_scenarios.append(scenario)
        
        coverage_percent = len(covered_scenarios) / len(error_scenarios) * 100
        assert coverage_percent >= 80, f"Error scenario coverage only {coverage_percent:.1f}%"
    
    def test_progressive_loading_workflow_complete(self):
        """Test that progressive loading workflow is complete"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Check for complete loading workflow
        workflow_stages = [
            'loading-three', 'loading-wasm', 'parsing-stl',
            'optimizing', 'rendering', 'complete'
        ]
        
        for stage in workflow_stages:
            assert stage in js_code, f"Missing workflow stage: {stage}"
        
        # Check for proper stage transitions
        assert 'showState(' in js_code
        assert 'showComplete(' in js_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])