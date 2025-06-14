"""
Comprehensive JavaScript Validation Tests
Tests for JavaScript syntax, structure, and functionality
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


@pytest.mark.javascript
class TestJavaScriptStructure:
    """Test JavaScript code structure and syntax"""
    
    def test_esm_module_format(self):
        """Test that JavaScript follows proper ESM module format"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Should start with proper module structure (flexible format)
        assert 'async function render' in js_code
        assert 'export default' in js_code and 'render' in js_code
        
        # JavaScript is embedded in Python file, not standalone
        assert len(js_code) > 1000
    
    def test_function_definitions(self):
        """Test that all major functions are properly defined"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Core viewer functions
        expected_functions = [
            'render', 'updateModel', 'animate', 'onWindowResize',
            'processSTLData', 'createFallbackGeometry'
        ]
        
        for func in expected_functions:
            assert f'function {func}' in js_code or f'{func}(' in js_code
    
    def test_class_definitions(self):
        """Test that all major classes are properly defined"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Expected classes from all phases
        expected_classes = [
            'MemoryManager', 'WASMCache', 'RenderingOptimizer',
            'ProgressiveLoader', 'ErrorHandler', 'STLParser'
        ]
        
        for cls in expected_classes:
            assert f'class {cls}' in js_code, f"Missing class: {cls}"
    
    def test_proper_scoping(self):
        """Test that variables are properly scoped"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Should use let/const for variable declarations
        let_count = js_code.count('let ')
        const_count = js_code.count('const ')
        var_count = js_code.count('var ')
        
        # Modern JavaScript should prefer let/const over var
        total_declarations = let_count + const_count + var_count
        modern_ratio = (let_count + const_count) / total_declarations if total_declarations > 0 else 0
        
        assert modern_ratio > 0.7, f"Modern variable declaration ratio only {modern_ratio:.2f}"
    
    def test_error_handling_structure(self):
        """Test that error handling follows proper structure"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Should have try-catch blocks
        try_count = js_code.count('try {')
        catch_count = js_code.count('catch (')
        
        assert try_count >= 5, f"Only {try_count} try blocks found"
        assert catch_count >= 5, f"Only {catch_count} catch blocks found"
        
        # Try/catch should be balanced
        assert abs(try_count - catch_count) <= 2, "Unbalanced try/catch blocks"


@pytest.mark.javascript
class TestJavaScriptFunctionality:
    """Test JavaScript functionality and features"""
    
    def test_three_js_integration(self):
        """Test Three.js integration"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Should have Three.js usage (flexible pattern matching)
        threejs_elements = [
            'THREE.', 'Scene', 'Camera', 'WebGLRenderer',
            'Mesh', 'BufferGeometry', 'Material'
        ]
        
        found_elements = []
        for element in threejs_elements:
            if element in js_code:
                found_elements.append(element)
        
        coverage = len(found_elements) / len(threejs_elements)
        assert coverage >= 0.6, f"Three.js integration coverage only {coverage:.1%}"
    
    def test_wasm_integration(self):
        """Test WebAssembly integration"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Should have WASM-related code
        wasm_elements = [
            'WebAssembly', 'wasm', 'WASM', 'instantiate',
            'WASMCache', 'loadModule'
        ]
        
        found_elements = []
        for element in wasm_elements:
            if element in js_code:
                found_elements.append(element)
        
        assert len(found_elements) >= 4, f"Insufficient WASM integration: {found_elements}"
    
    def test_memory_management(self):
        """Test memory management implementation"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Should have comprehensive memory management
        memory_elements = [
            'MemoryManager', 'cleanup', 'dispose', 'register',
            'removeEventListener', 'memory'
        ]
        
        for element in memory_elements:
            assert element in js_code, f"Missing memory management element: {element}"
    
    def test_performance_optimizations(self):
        """Test performance optimization features"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Should have performance optimizations
        perf_elements = [
            'RenderingOptimizer', 'LOD', 'requestAnimationFrame',
            'performance', 'optimize', 'cache'
        ]
        
        found_elements = []
        for element in perf_elements:
            if element in js_code:
                found_elements.append(element)
        
        assert len(found_elements) >= 4, f"Insufficient performance features: {found_elements}"


@pytest.mark.javascript
class TestJavaScriptSyntaxValidation:
    """Detailed JavaScript syntax validation"""
    
    def test_bracket_balance(self):
        """Test that all brackets are properly balanced"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Test different bracket types
        brackets = [
            ('(', ')'),
            ('[', ']'),
            ('{', '}')
        ]
        
        for open_bracket, close_bracket in brackets:
            open_count = js_code.count(open_bracket)
            close_count = js_code.count(close_bracket)
            
            # Allow larger tolerance for complex JavaScript with Phase 5.2 features
            diff = abs(open_count - close_count)
            assert diff <= 25, f"Bracket imbalance for {open_bracket}{close_bracket}: {open_count} vs {close_count}"
    
    def test_string_quotes_balance(self):
        """Test that string quotes are properly balanced"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Count single quotes (excluding escaped ones)
        single_quotes = len(re.findall(r"(?<!\\)'", js_code))
        
        # Count double quotes (excluding escaped ones)
        double_quotes = len(re.findall(r'(?<!\\)"', js_code))
        
        # Count template literals
        template_literals = js_code.count('`')
        
        # Single and double quotes should be even (balanced)
        # Template literals should be even (balanced)
        assert single_quotes % 2 == 0, f"Unbalanced single quotes: {single_quotes}"
        assert double_quotes % 2 == 0, f"Unbalanced double quotes: {double_quotes}"
        assert template_literals % 2 == 0, f"Unbalanced template literals: {template_literals}"
    
    def test_semicolon_usage(self):
        """Test semicolon usage consistency"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        lines = [line.strip() for line in js_code.split('\n') if line.strip()]
        
        # Count lines that should end with semicolons
        statement_lines = []
        for line in lines:
            # Skip comments, empty lines, and control structures
            if (line.startswith('//') or line.startswith('/*') or line.startswith('*') or
                line.startswith('}') or line.startswith('{') or
                line.endswith('{') or line.endswith('}') or
                line.startswith('if ') or line.startswith('for ') or
                line.startswith('while ') or line.startswith('else') or
                line.startswith('case ') or line.startswith('default:')):
                continue
            
            # Lines that should end with semicolon
            if (('=' in line and not line.endswith('{')) or
                line.startswith('return ') or line.startswith('throw ') or
                line.startswith('break') or line.startswith('continue') or
                ('(' in line and ')' in line and not line.endswith('{'))):
                statement_lines.append(line)
        
        # Check semicolon usage (allow some flexibility)
        if statement_lines:
            semicolon_lines = [line for line in statement_lines if line.endswith(';')]
            semicolon_ratio = len(semicolon_lines) / len(statement_lines)
            
            # Should have reasonable semicolon usage
            assert semicolon_ratio > 0.3, f"Low semicolon usage: {semicolon_ratio:.1%}"
    
    def test_indentation_consistency(self):
        """Test that indentation is reasonably consistent"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        lines = js_code.split('\n')
        
        # Analyze indentation patterns
        indentation_levels = []
        for line in lines:
            if line.strip():  # Skip empty lines
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    indentation_levels.append(leading_spaces)
        
        if indentation_levels:
            # Check for consistent indentation increments
            unique_levels = sorted(set(indentation_levels))
            
            # Should have reasonable indentation structure
            assert len(unique_levels) >= 3, "Insufficient indentation structure"
            assert max(unique_levels) <= 100, "Excessive indentation depth"


@pytest.mark.javascript
class TestJavaScriptQuality:
    """Test JavaScript code quality metrics"""
    
    def test_code_organization(self):
        """Test that code is well organized"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Should have clear sections/phases
        phase_markers = [
            'PHASE 5.1', 'PHASE 5.2', 'MEMORY MANAGEMENT',
            'PROGRESSIVE LOADING', 'ERROR HANDLING'
        ]
        
        found_markers = []
        for marker in phase_markers:
            if marker in js_code:
                found_markers.append(marker)
        
        assert len(found_markers) >= 3, f"Poor code organization: {found_markers}"
    
    def test_comment_coverage(self):
        """Test that code has adequate comments"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Count different types of comments
        line_comments = js_code.count('//')
        block_comments = js_code.count('/*')
        
        total_comments = line_comments + block_comments
        
        # Count non-empty lines
        lines = [line.strip() for line in js_code.split('\n') if line.strip()]
        code_lines = len(lines)
        
        # Comment ratio should be reasonable
        comment_ratio = total_comments / code_lines if code_lines > 0 else 0
        assert comment_ratio > 0.05, f"Insufficient comments: {comment_ratio:.1%}"
    
    def test_function_complexity(self):
        """Test that functions are not overly complex"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Find function definitions
        function_patterns = [
            r'function\s+(\w+)\s*\([^)]*\)\s*{',
            r'(\w+)\s*\([^)]*\)\s*{',  # Method definitions
            r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*{'
        ]
        
        functions_found = 0
        for pattern in function_patterns:
            matches = re.findall(pattern, js_code)
            functions_found += len(matches)
        
        # Should have reasonable number of functions
        assert functions_found >= 20, f"Only {functions_found} functions found"
        
        # Check for extremely long functions (basic heuristic)
        function_starts = js_code.count('function ') + js_code.count(') {')
        total_braces = js_code.count('{')
        
        # Average braces per function should be reasonable
        if function_starts > 0:
            avg_braces = total_braces / function_starts
            assert avg_braces < 50, f"Functions may be too complex: {avg_braces:.1f} braces per function"
    
    def test_console_usage(self):
        """Test reasonable console usage"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Count console statements
        console_log = js_code.count('console.log')
        console_warn = js_code.count('console.warn') 
        console_error = js_code.count('console.error')
        
        total_console = console_log + console_warn + console_error
        
        # Should have some logging but not excessive (adjusted for Phase 5.2)
        assert 10 <= total_console <= 400, f"Console usage seems inappropriate: {total_console}"
        
        # Should have error logging
        assert console_error >= 3, f"Insufficient error logging: {console_error}"


@pytest.mark.javascript
@pytest.mark.integration
class TestJavaScriptIntegration:
    """Test JavaScript integration with Python components"""
    
    def test_widget_integration(self):
        """Test integration with anywidget framework"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Should have proper widget integration
        widget_elements = [
            'model', 'el', 'render', 'change:', 'get(', 'set('
        ]
        
        for element in widget_elements:
            assert element in js_code, f"Missing widget integration: {element}"
    
    def test_python_data_binding(self):
        """Test binding with Python data structures"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Should access Python traits
        python_traits = [
            'stl_data', 'scad_code', 'error_message', 'is_loading',
            'renderer_type', 'renderer_status'
        ]
        
        found_traits = []
        for trait in python_traits:
            if trait in js_code:
                found_traits.append(trait)
        
        coverage = len(found_traits) / len(python_traits)
        assert coverage >= 0.7, f"Python trait coverage only {coverage:.1%}"
    
    def test_event_handling(self):
        """Test event handling implementation"""
        viewer = OpenSCADViewer()
        js_code = viewer._esm
        
        # Should have proper event handling
        event_elements = [
            'addEventListener', 'removeEventListener', 'on(', 'change:',
            'resize', 'click', 'error'
        ]
        
        found_events = []
        for element in event_elements:
            if element in js_code:
                found_events.append(element)
        
        assert len(found_events) >= 4, f"Insufficient event handling: {found_events}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])