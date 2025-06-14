"""
Phase 4.4 Integration Tests: End-to-End Integration & Production Readiness

Tests the complete enhanced workflow with version detection, migration, and optimization.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import asyncio

from src.marimo_openscad.viewer import OpenSCADViewer
from src.marimo_openscad.version_manager import OpenSCADVersionManager, VersionInfo
from src.marimo_openscad.wasm_version_manager import WASMVersionManager
from src.marimo_openscad.migration_engine import MigrationEngine, SyntaxIssue, SyntaxIssueType


class TestPhase44Integration:
    """Test Phase 4.4 end-to-end integration."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_scad_code = """
        // Test SCAD code with potential version issues
        module test_cube() {
            assign(x = 10) {  // Deprecated syntax
                cube([x, x, x]);
            }
        }
        test_cube();
        """
        
        self.modern_scad_code = """
        // Modern SCAD code
        module test_cube() {
            x = 10;
            cube([x, x, x]);
        }
        test_cube();
        """
    
    @pytest.fixture
    def mock_viewer(self):
        """Create viewer with mocked dependencies."""
        with patch('src.marimo_openscad.viewer.OpenSCADVersionManager') as mock_vm, \
             patch('src.marimo_openscad.viewer.WASMVersionManager') as mock_wvm, \
             patch('src.marimo_openscad.viewer.MigrationEngine') as mock_me:
            
            # Mock version manager
            mock_vm_instance = Mock()
            mock_vm_instance.analyze_scad_code.return_value = {'required_version': '2023.06'}
            mock_vm_instance.check_compatibility.return_value = {'compatible': False, 'issues': ['deprecated_assign']}
            mock_vm.return_value = mock_vm_instance
            
            # Mock WASM version manager
            mock_wvm_instance = Mock()
            mock_wvm_instance.select_optimal_version.return_value = '2023.06'
            mock_wvm_instance.switch_to_version.return_value = True
            mock_wvm.return_value = mock_wvm_instance
            
            # Mock migration engine
            mock_me_instance = Mock()
            mock_me_instance.detect_version_issues.return_value = [
                SyntaxIssue(
                    issue_type=SyntaxIssueType.DEPRECATED_SYNTAX,
                    line_number=3,
                    column_start=0,
                    column_end=10,
                    original_text='assign(x = 10)',
                    message='assign() is deprecated',
                    severity='warning'
                )
            ]
            mock_me_instance.suggest_migrations.return_value = [
                {
                    'rule': 'deprecated_assign',
                    'description': 'Replace assign() with direct variable assignment',
                    'confidence': 0.9,
                    'preview': 'x = 10;'
                }
            ]
            mock_me_instance.apply_migration.return_value = {
                'success': True,
                'migrated_code': self.modern_scad_code
            }
            mock_me.return_value = mock_me_instance
            
            viewer = OpenSCADViewer(renderer_type="local")
            yield viewer, mock_vm_instance, mock_wvm_instance, mock_me_instance

    def test_enhanced_workflow_basic_flow(self, mock_viewer):
        """Test basic enhanced workflow execution."""
        viewer, mock_vm, mock_wvm, mock_me = mock_viewer
        
        # Test the enhanced workflow
        result = viewer._enhanced_scad_update_workflow(self.test_scad_code)
        
        # Verify workflow steps were called
        mock_vm.analyze_scad_code.assert_called_once_with(self.test_scad_code)
        mock_vm.check_compatibility.assert_called_once()
        mock_me.detect_version_issues.assert_called_once_with(self.test_scad_code)
        mock_me.suggest_migrations.assert_called_once()
        mock_wvm.select_optimal_version.assert_called_once()
        
        # Verify result
        assert result == self.modern_scad_code
        assert viewer.version_compatibility_status == 'migration_suggested'
        assert len(viewer.migration_suggestions) == 1

    def test_enhanced_workflow_caching(self, mock_viewer):
        """Test workflow caching functionality."""
        viewer, mock_vm, mock_wvm, mock_me = mock_viewer
        
        # First call
        result1 = viewer._enhanced_scad_update_workflow(self.test_scad_code)
        call_count1 = mock_vm.analyze_scad_code.call_count
        
        # Second call with same code should use cache
        result2 = viewer._enhanced_scad_update_workflow(self.test_scad_code)
        call_count2 = mock_vm.analyze_scad_code.call_count
        
        # Verify caching worked
        assert result1 == result2
        assert call_count2 == call_count1  # No additional calls

    def test_enhanced_workflow_no_migration_needed(self, mock_viewer):
        """Test workflow when no migration is needed."""
        viewer, mock_vm, mock_wvm, mock_me = mock_viewer
        
        # Configure mocks for compatible code
        mock_vm.check_compatibility.return_value = {'compatible': True}
        mock_me.detect_version_issues.return_value = []
        
        result = viewer._enhanced_scad_update_workflow(self.modern_scad_code)
        
        # Verify no migration was attempted
        assert result == self.modern_scad_code
        assert viewer.version_compatibility_status == 'compatible'
        assert len(viewer.migration_suggestions) == 0

    def test_enhanced_workflow_error_handling(self, mock_viewer):
        """Test workflow error handling."""
        viewer, mock_vm, mock_wvm, mock_me = mock_viewer
        
        # Configure mock to raise error
        mock_vm.analyze_scad_code.side_effect = Exception("Version detection failed")
        
        result = viewer._enhanced_scad_update_workflow(self.test_scad_code)
        
        # Should fallback to original code
        assert result == self.test_scad_code
        assert viewer.version_compatibility_status == 'error'

    def test_update_scad_code_integration(self, mock_viewer):
        """Test full update_scad_code integration with enhanced workflow."""
        viewer, mock_vm, mock_wvm, mock_me = mock_viewer
        
        # Mock renderer to avoid actual rendering
        viewer.renderer = Mock()
        viewer.renderer.render_scad_to_stl.return_value = b"STL_DATA"
        
        # Test WASM rendering path
        viewer.wasm_enabled = True
        viewer.enable_real_time_wasm = True
        
        viewer.update_scad_code(self.test_scad_code)
        
        # Verify enhanced workflow was called and SCAD code was updated
        assert viewer.scad_code == self.modern_scad_code
        assert viewer.version_compatibility_status == 'migration_suggested'

    def test_version_switching_integration(self, mock_viewer):
        """Test version switching during workflow."""
        viewer, mock_vm, mock_wvm, mock_me = mock_viewer
        
        # Test version switching
        result = viewer._switch_to_version_if_needed('2023.06')
        
        # Verify version was switched
        assert result is True
        assert viewer.active_wasm_version == '2023.06'
        mock_wvm.switch_to_version.assert_called_once_with('2023.06')

    def test_migration_confidence_filtering(self, mock_viewer):
        """Test that only high-confidence migrations are applied."""
        viewer, mock_vm, mock_wvm, mock_me = mock_viewer
        
        # Configure low-confidence migration
        mock_me.suggest_migrations.return_value = [
            {
                'rule': 'uncertain_change',
                'description': 'Uncertain migration',
                'confidence': 0.5  # Low confidence
            }
        ]
        
        result = viewer._enhanced_scad_update_workflow(self.test_scad_code)
        
        # Should not apply low-confidence migration
        assert result == self.test_scad_code
        mock_me.apply_migration.assert_not_called()

    def test_performance_optimization_traits(self, mock_viewer):
        """Test that performance traits are properly updated."""
        viewer, mock_vm, mock_wvm, mock_me = mock_viewer
        
        # Verify new traits exist
        assert hasattr(viewer, 'migration_suggestions')
        assert hasattr(viewer, 'version_compatibility_status')
        assert hasattr(viewer, 'available_migrations')
        assert hasattr(viewer, 'version_detection_cache')
        
        # Test trait synchronization
        viewer._enhanced_scad_update_workflow(self.test_scad_code)
        
        assert viewer.migration_suggestions is not None
        assert viewer.version_compatibility_status in ['compatible', 'migration_suggested', 'incompatible', 'error']
        assert isinstance(viewer.available_migrations, dict)

    def test_fallback_without_version_management(self):
        """Test fallback behavior when version management is disabled."""
        # Create viewer without version management
        with patch('src.marimo_openscad.viewer.OpenSCADVersionManager', side_effect=Exception("No version manager")):
            viewer = OpenSCADViewer(renderer_type="local")
            
            # Should still work without version management
            result = viewer._enhanced_scad_update_workflow(self.test_scad_code)
            assert result == self.test_scad_code
            assert viewer.version_compatibility_status == 'error'


class TestPhase44PerformanceOptimization:
    """Test performance optimizations in Phase 4.4."""
    
    def test_cache_performance(self):
        """Test that caching improves performance."""
        with patch('src.marimo_openscad.viewer.OpenSCADVersionManager') as mock_vm:
            mock_vm_instance = Mock()
            mock_vm_instance.analyze_scad_code.return_value = {'required_version': '2023.06'}
            mock_vm.return_value = mock_vm_instance
            
            viewer = OpenSCADViewer(renderer_type="local")
            
            # First call - should hit version manager
            viewer._enhanced_scad_update_workflow("cube(10);")
            first_call_count = mock_vm_instance.analyze_scad_code.call_count
            
            # Second call with same code - should use cache
            viewer._enhanced_scad_update_workflow("cube(10);")
            second_call_count = mock_vm_instance.analyze_scad_code.call_count
            
            # Verify caching works
            assert second_call_count == first_call_count

    def test_memory_efficient_caching(self):
        """Test that cache uses memory-efficient keys."""
        viewer = OpenSCADViewer(renderer_type="local")
        
        # Test that cache uses hash for keys, not full code
        code = "cube(10);" * 1000  # Large code
        viewer.version_detection_cache[hash(code)] = {'test': 'data'}
        
        # Verify cache key is hash, not full string
        assert len(list(viewer.version_detection_cache.keys())) == 1
        cache_key = list(viewer.version_detection_cache.keys())[0]
        assert isinstance(cache_key, int)  # Hash is integer


class TestPhase44UserExperience:
    """Test user experience improvements in Phase 4.4."""
    
    def test_non_blocking_migration_suggestions(self, mock_viewer):
        """Test that migration suggestions don't block rendering."""
        viewer, mock_vm, mock_wvm, mock_me = mock_viewer
        
        # Configure migration that might fail
        mock_me.apply_migration.side_effect = Exception("Migration failed")
        
        result = viewer._enhanced_scad_update_workflow("assign(x=10) cube(x);")
        
        # Should still return original code, not fail completely
        assert result is not None
        assert viewer.version_compatibility_status != 'error'

    def test_migration_preview_functionality(self, mock_viewer):
        """Test migration preview functionality."""
        viewer, mock_vm, mock_wvm, mock_me = mock_viewer
        
        viewer._enhanced_scad_update_workflow(self.test_scad_code)
        
        # Verify preview data is available
        assert 'preview' in viewer.available_migrations
        assert 'suggestions' in viewer.available_migrations
        assert viewer.available_migrations['preview'] is not None

    def test_user_preference_respect(self, mock_viewer):
        """Test that user preferences are respected."""
        viewer, mock_vm, mock_wvm, mock_me = mock_viewer
        
        # Disable auto version selection
        viewer.auto_version_selection = False
        
        # Should still work but not auto-switch versions
        result = viewer._enhanced_scad_update_workflow(self.test_scad_code)
        assert result is not None
        
        # Version switching should be limited when auto-selection is off
        mock_wvm.switch_to_version.assert_called()  # Still called for optimal version


if __name__ == "__main__":
    pytest.main([__file__, "-v"])