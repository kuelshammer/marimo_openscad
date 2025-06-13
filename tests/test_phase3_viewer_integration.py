#!/usr/bin/env python3
"""
Phase 3 Viewer Integration Tests

Tests the actual AsyncOpenSCADViewer implementation with
async communication and fallback capabilities.
"""

import pytest
import asyncio
import time
import os
import sys
from unittest.mock import AsyncMock, Mock, patch

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestPhase3ViewerIntegration:
    """Test Phase 3 viewer implementation"""
    
    @pytest.mark.asyncio
    async def test_phase3_viewer_creation(self):
        """Test Phase 3 viewer can be created and initialized"""
        print("🔍 Testing Phase 3 viewer creation...")
        
        try:
            from marimo_openscad.viewer_phase3 import openscad_viewer_phase3
            from solid2 import cube
        except ImportError as e:
            pytest.skip(f"Phase 3 viewer not available: {e}")
        
        # Test viewer creation
        test_cube = cube([2, 2, 2])
        
        start_time = time.perf_counter()
        viewer = openscad_viewer_phase3(test_cube, renderer_type="auto")
        creation_time = time.perf_counter() - start_time
        
        print(f"  ✅ Viewer created in {creation_time:.3f}s")
        
        # Test basic attributes
        assert hasattr(viewer, 'async_enabled'), "Viewer should have async_enabled attribute"
        assert hasattr(viewer, 'message_bus'), "Viewer should have message bus"
        assert hasattr(viewer, 'request_timeout'), "Viewer should have request timeout"
        
        # Test async communication attributes
        assert viewer.async_enabled == True, "Async should be enabled by default"
        assert viewer.request_timeout == 10.0, "Default timeout should be 10 seconds"
        assert viewer.renderer_type == "auto", "Renderer type should be auto"
        
        # Test message bus initialization
        assert viewer.message_bus is not None, "Message bus should be initialized"
        assert hasattr(viewer.message_bus, 'create_request_id'), "Message bus should have request ID creation"
        assert hasattr(viewer.message_bus, 'send_request'), "Message bus should have send_request method"
        
        print("✅ Phase 3 viewer creation validated")
    
    @pytest.mark.asyncio
    async def test_async_message_bus_functionality(self):
        """Test async message bus core functionality"""
        print("🔍 Testing async message bus functionality...")
        
        try:
            from marimo_openscad.viewer_phase3 import AsyncMessageBus, AsyncCommunicationError
        except ImportError as e:
            pytest.skip(f"Phase 3 components not available: {e}")
        
        # Test message bus creation
        message_bus = AsyncMessageBus()
        
        # Test request ID generation
        request_id1 = message_bus.create_request_id()
        request_id2 = message_bus.create_request_id()
        
        assert request_id1 != request_id2, "Request IDs should be unique"
        assert len(request_id1) == 36, "Request ID should be valid UUID format"  # UUID length
        
        print(f"  ✅ Unique request IDs generated: {request_id1[:8]}... vs {request_id2[:8]}...")
        
        # Test request/response handling
        mock_widget = Mock()
        mock_widget._send_message_to_js = AsyncMock()
        
        # Test successful request handling
        test_data = {"scad_code": "cube([1,1,1]);"}
        
        # Simulate async request (will timeout since we don't have real JS response)
        with pytest.raises(AsyncCommunicationError) as exc_info:
            await message_bus.send_request(mock_widget, "render_request", test_data, timeout=0.1)
        
        # Verify timeout error
        assert exc_info.value.error_type == "timeout_error", "Should raise timeout error"
        assert "timed out" in str(exc_info.value), "Error message should mention timeout"
        
        print("  ✅ Timeout handling validated")
        
        # Test response handling
        test_response = {
            "id": request_id1,
            "status": "success",
            "stl_data": "test STL data",
            "timestamp": time.time()
        }
        
        # Add pending request manually for testing
        future = asyncio.get_event_loop().create_future()
        message_bus.pending_requests[request_id1] = future
        
        # Handle response
        message_bus.handle_response(test_response)
        
        # Check that future was resolved
        assert future.done(), "Future should be resolved after response"
        result = await future
        assert result == test_response, "Response should match test data"
        
        print("  ✅ Response handling validated")
        print("✅ Async message bus functionality validated")
    
    @pytest.mark.asyncio 
    async def test_viewer_async_update(self):
        """Test async model update functionality"""
        print("🔍 Testing viewer async model update...")
        
        try:
            from marimo_openscad.viewer_phase3 import openscad_viewer_phase3
            from solid2 import cube
        except ImportError as e:
            pytest.skip(f"Phase 3 viewer not available: {e}")
        
        # Create viewer without initial model
        viewer = openscad_viewer_phase3(None, renderer_type="auto")
        
        # Test initial state
        assert viewer.scad_code == "", "Initial SCAD code should be empty"
        assert viewer.stl_data == "", "Initial STL data should be empty"
        assert viewer.is_loading == False, "Should not be loading initially"
        
        # Test async model update
        test_cube = cube([3, 3, 3])
        
        # Mock the async communication to avoid actual JS calls
        original_send = viewer._send_message_to_js
        viewer._send_message_to_js = AsyncMock()
        
        # Update model asynchronously
        start_time = time.perf_counter()
        await viewer.update_model_async(test_cube)
        update_time = time.perf_counter() - start_time
        
        print(f"  ✅ Async update completed in {update_time:.3f}s")
        
        # Verify SCAD code was set
        assert viewer.scad_code != "", "SCAD code should be generated"
        assert "cube" in viewer.scad_code, "SCAD code should contain cube"
        
        # Verify loading state was managed
        assert viewer.is_loading == False, "Loading should be complete"
        
        # Since we mocked JS communication, it should fall back to sync rendering
        # The renderer_status should indicate the fallback was used
        print(f"  Renderer status: {viewer.renderer_status}")
        print(f"  STL data length: {len(viewer.stl_data)}")
        print(f"  Error message: {viewer.error_message}")
        
        # Restore original method
        viewer._send_message_to_js = original_send
        
        print("✅ Viewer async update validated")
    
    @pytest.mark.asyncio
    async def test_phase3_widget_attributes(self):
        """Test Phase 3 specific widget attributes and methods"""
        print("🔍 Testing Phase 3 widget attributes...")
        
        try:
            from marimo_openscad.viewer_phase3 import openscad_viewer_phase3
            from solid2 import cube
        except ImportError as e:
            pytest.skip(f"Phase 3 viewer not available: {e}")
        
        viewer = openscad_viewer_phase3(cube([1, 1, 1]))
        
        # Test Phase 3 specific traits
        phase3_traits = ['async_enabled', 'request_timeout', 'performance_mode']
        for trait in phase3_traits:
            assert hasattr(viewer, trait), f"Viewer should have {trait} trait"
        
        # Test CSS and ESM generation
        css_content = viewer._css
        esm_content = viewer._esm
        
        assert len(css_content) > 0, "CSS content should be generated"
        assert len(esm_content) > 0, "ESM content should be generated"
        
        # Check for Phase 3 specific content
        assert "phase3" in css_content.lower(), "CSS should mention Phase 3"
        assert "async" in esm_content.lower(), "ESM should mention async"
        assert "message" in esm_content.lower(), "ESM should mention messaging"
        
        print(f"  ✅ CSS content: {len(css_content)} characters")
        print(f"  ✅ ESM content: {len(esm_content)} characters")
        
        # Test async capabilities
        assert viewer.async_enabled == True, "Async should be enabled"
        assert callable(viewer.update_model_async), "Should have async update method"
        assert hasattr(viewer.message_bus, 'send_request'), "Should have message bus with send_request"
        
        print("✅ Phase 3 widget attributes validated")
    
    def test_phase3_sync_compatibility(self):
        """Test Phase 3 maintains sync compatibility with Phase 2"""
        print("🔍 Testing Phase 3 sync compatibility...")
        
        try:
            from marimo_openscad.viewer_phase3 import openscad_viewer_phase3
            from solid2 import cube
        except ImportError as e:
            pytest.skip(f"Phase 3 viewer not available: {e}")
        
        # Test synchronous model update (should create async task)
        viewer = openscad_viewer_phase3(None)
        test_cube = cube([1, 1, 1])
        
        # This should work without async/await (backward compatibility)
        viewer.update_model(test_cube)
        
        # Give async task time to start
        import time
        time.sleep(0.1)
        
        # Verify model was updated
        assert viewer.scad_code != "", "SCAD code should be set via sync method"
        
        print("  ✅ Sync compatibility maintained")
        print("✅ Phase 3 sync compatibility validated")


if __name__ == "__main__":
    # Allow running individual tests
    pytest.main([__file__, "-v", "-s"])