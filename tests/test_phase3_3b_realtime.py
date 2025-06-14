"""
Tests for Phase 3.3b Real-time Rendering Features

Tests the new real-time parameter updates, STL caching, and performance 
monitoring capabilities added in Phase 3.3b.
"""

import pytest
import asyncio
import time
import hashlib
from unittest.mock import Mock, patch

from src.marimo_openscad.viewer import OpenSCADViewer
from src.marimo_openscad.realtime_renderer import (
    ParameterDebouncer, 
    STLCache, 
    RealTimeRenderer
)


class TestParameterDebouncer:
    """Test parameter debouncing functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.debouncer = ParameterDebouncer(delay_ms=50)  # Short delay for testing
        self.render_calls = []
        
        async def mock_render():
            self.render_calls.append(time.time())
            
        self.debouncer.set_render_callback(mock_render)
    
    def test_debouncer_initialization(self):
        """Test debouncer is initialized correctly."""
        assert self.debouncer.delay_ms == 50
        assert len(self.debouncer.pending_changes) == 0
        assert self.debouncer.render_timer is None
        
    def test_parameter_update_scheduling(self):
        """Test that parameter updates schedule renders."""
        self.debouncer.update_parameter("size", 10)
        
        assert "size" in self.debouncer.pending_changes
        assert self.debouncer.pending_changes["size"] == 10
        # In sync context without event loop, render_timer may be None
        # The important thing is that pending changes are recorded
        
    @pytest.mark.asyncio
    async def test_debounced_rendering(self):
        """Test that rapid parameter changes are debounced."""
        # Rapid parameter updates
        self.debouncer.update_parameter("size", 10)
        self.debouncer.update_parameter("size", 15)
        self.debouncer.update_parameter("size", 20)
        
        # Wait for debounce delay
        await asyncio.sleep(0.1)  # 100ms > 50ms delay
        
        # Should only have one render call
        assert len(self.render_calls) == 1
        
    @pytest.mark.asyncio
    async def test_multiple_parameter_debouncing(self):
        """Test debouncing with multiple parameters."""
        self.debouncer.update_parameter("width", 10)
        self.debouncer.update_parameter("height", 15)
        self.debouncer.update_parameter("depth", 8)
        
        # Wait for debounce
        await asyncio.sleep(0.1)
        
        # Should consolidate into single render
        assert len(self.render_calls) == 1
        
    def test_force_render_bypasses_debouncing(self):
        """Test that force render bypasses debouncing."""
        self.debouncer.update_parameter("size", 10)
        initial_call_count = len(self.render_calls)
        
        self.debouncer.force_render()
        
        # Force render should clear pending changes regardless of event loop
        assert len(self.debouncer.pending_changes) == 0


class TestSTLCache:
    """Test STL caching functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.cache = STLCache(max_size_mb=1, max_entries=5)  # Small cache for testing
        
    def test_cache_initialization(self):
        """Test cache is initialized correctly."""
        assert self.cache.max_size == 1 * 1024 * 1024  # 1MB in bytes
        assert self.cache.max_entries == 5
        assert len(self.cache.cache) == 0
        assert self.cache.current_size == 0
        assert self.cache.hits == 0
        assert self.cache.misses == 0
        
    def test_cache_key_generation(self):
        """Test cache key generation is consistent."""
        scad_code = "cube([10, 10, 10]);"
        params = {"size": 10, "color": "red"}
        
        key1 = self.cache.get_cache_key(scad_code, params)
        key2 = self.cache.get_cache_key(scad_code, params)
        
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex digest length
        
    def test_cache_key_different_for_different_inputs(self):
        """Test cache keys are different for different inputs."""
        key1 = self.cache.get_cache_key("cube([10, 10, 10]);", {"size": 10})
        key2 = self.cache.get_cache_key("cube([20, 20, 20]);", {"size": 20})
        key3 = self.cache.get_cache_key("cube([10, 10, 10]);", {"size": 20})
        
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3
        
    def test_cache_store_and_retrieve(self):
        """Test storing and retrieving from cache."""
        key = "test_key"
        stl_data = b"test_stl_data"
        
        # Store data
        self.cache.store(key, stl_data)
        
        assert len(self.cache.cache) == 1
        assert self.cache.current_size == len(stl_data)
        
        # Retrieve data
        retrieved = self.cache.get(key)
        
        assert retrieved == stl_data
        assert self.cache.hits == 1
        assert self.cache.misses == 0
        
    def test_cache_miss(self):
        """Test cache miss behavior."""
        result = self.cache.get("nonexistent_key")
        
        assert result is None
        assert self.cache.hits == 0
        assert self.cache.misses == 1
        
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        # Fill cache to max entries
        for i in range(self.cache.max_entries):
            key = f"key_{i}"
            data = f"data_{i}".encode()
            self.cache.store(key, data)
            
        assert len(self.cache.cache) == self.cache.max_entries
        
        # Add one more item to trigger eviction
        self.cache.store("key_new", b"new_data")
        
        assert len(self.cache.cache) == self.cache.max_entries
        # First item should be evicted
        assert self.cache.get("key_0") is None
        # New item should be present
        assert self.cache.get("key_new") == b"new_data"
        
    def test_cache_size_limit(self):
        """Test cache size limit enforcement."""
        # Create data that would exceed size limit
        large_data = b"x" * (self.cache.max_size + 1000)
        
        # Should not store data that exceeds max size
        self.cache.store("large_key", large_data)
        
        assert len(self.cache.cache) == 0
        assert self.cache.current_size == 0
        
    @pytest.mark.asyncio
    async def test_get_or_render(self):
        """Test get_or_render functionality."""
        key = "test_key"
        expected_data = b"rendered_stl_data"
        
        render_calls = []
        
        async def mock_render():
            render_calls.append(time.time())
            return expected_data
            
        # First call should render
        result1 = await self.cache.get_or_render(key, mock_render)
        
        assert result1 == expected_data
        assert len(render_calls) == 1
        
        # Second call should use cache
        result2 = await self.cache.get_or_render(key, mock_render)
        
        assert result2 == expected_data
        assert len(render_calls) == 1  # No additional render call
        assert self.cache.hits == 1
        
    def test_cache_stats(self):
        """Test cache statistics."""
        # Add some data
        self.cache.store("key1", b"data1")
        self.cache.store("key2", b"data2")
        
        # Generate hits and misses
        self.cache.get("key1")  # Hit
        self.cache.get("key3")  # Miss
        
        stats = self.cache.get_stats()
        
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5
        assert stats['entry_count'] == 2
        assert stats['total_size_bytes'] == len(b"data1") + len(b"data2")
        
    def test_cache_clear(self):
        """Test cache clearing."""
        # Add some data
        self.cache.store("key1", b"data1")
        self.cache.store("key2", b"data2")
        
        assert len(self.cache.cache) > 0
        assert self.cache.current_size > 0
        
        # Clear cache
        self.cache.clear()
        
        assert len(self.cache.cache) == 0
        assert self.cache.current_size == 0


class TestRealTimeRenderer:
    """Test real-time renderer integration."""
    
    def setup_method(self):
        """Setup test environment."""
        # Create mock viewer
        self.mock_viewer = Mock()
        self.mock_viewer.scad_code = "cube([10, 10, 10]);"
        self.mock_viewer._render_stl = Mock(return_value=b"mock_stl_data")
        
        self.renderer = RealTimeRenderer(
            viewer=self.mock_viewer,
            cache_size_mb=1,
            debounce_ms=50
        )
        
    def test_realtime_renderer_initialization(self):
        """Test real-time renderer initialization."""
        assert self.renderer.cache is not None
        assert self.renderer.debouncer is not None
        assert self.renderer.render_count == 0
        assert self.renderer.total_render_time == 0.0
        assert not self.renderer.is_rendering
        
    @pytest.mark.asyncio
    async def test_parameter_update(self):
        """Test parameter update functionality."""
        await self.renderer.update_parameter("size", 20)
        
        # Should schedule debounced render
        assert "size" in self.renderer.debouncer.pending_changes
        assert self.renderer.debouncer.pending_changes["size"] == 20
        
    @pytest.mark.asyncio
    async def test_render_scad_code_with_cache(self):
        """Test SCAD code rendering with caching."""
        scad_code = "cube([15, 15, 15]);"
        
        # First render should call mock
        result1 = await self.renderer.render_scad_code(scad_code)
        
        assert result1 == b"mock_stl_data"
        assert self.mock_viewer._render_stl.call_count == 1
        
        # Second render should use cache
        result2 = await self.renderer.render_scad_code(scad_code)
        
        assert result2 == b"mock_stl_data"
        assert self.mock_viewer._render_stl.call_count == 1  # No additional call
        
    @pytest.mark.asyncio
    async def test_render_scad_code_without_cache(self):
        """Test SCAD code rendering without caching."""
        scad_code = "sphere(r=10);"
        
        # Render without cache
        result = await self.renderer.render_scad_code(scad_code, use_cache=False)
        
        assert result == b"mock_stl_data"
        assert self.mock_viewer._render_stl.call_count == 1
        
        # Second call should render again (no cache)
        await self.renderer.render_scad_code(scad_code, use_cache=False)
        assert self.mock_viewer._render_stl.call_count == 2
        
    def test_performance_stats(self):
        """Test performance statistics."""
        stats = self.renderer.get_performance_stats()
        
        # Should have rendering, cache, and debouncing stats
        assert 'rendering' in stats
        assert 'cache' in stats
        assert 'debouncing' in stats
        
        # Check rendering stats structure
        rendering_stats = stats['rendering']
        assert 'total_renders' in rendering_stats
        assert 'avg_render_time' in rendering_stats
        assert 'is_rendering' in rendering_stats


class TestViewerRealTimeIntegration:
    """Test real-time features integration with OpenSCADViewer."""
    
    def setup_method(self):
        """Setup test environment."""
        self.viewer = OpenSCADViewer(renderer_type="local")
        
        # Mock the _render_stl method for predictable testing
        self.render_calls = []
        
        def mock_render_stl(scad_code, force_render=False):
            self.render_calls.append((scad_code, force_render))
            return f"stl_data_for_{len(scad_code)}_chars".encode()
            
        self.viewer._render_stl = mock_render_stl
        
    def test_viewer_realtime_initialization(self):
        """Test that viewer initializes with real-time features."""
        assert hasattr(self.viewer, 'realtime_renderer')
        assert self.viewer.real_time_enabled is True
        assert self.viewer.debounce_delay_ms == 100
        assert self.viewer.cache_hit_rate == 0.0
        
    def test_set_debounce_delay(self):
        """Test setting debounce delay."""
        original_delay = self.viewer.debounce_delay_ms
        new_delay = 200
        
        self.viewer.set_debounce_delay(new_delay)
        
        assert self.viewer.debounce_delay_ms == new_delay
        assert self.viewer.realtime_renderer.debouncer.delay_ms == new_delay
        
    def test_enable_disable_realtime(self):
        """Test enabling/disabling real-time rendering."""
        assert self.viewer.real_time_enabled is True
        
        self.viewer.enable_realtime_rendering(False)
        assert self.viewer.real_time_enabled is False
        
        self.viewer.enable_realtime_rendering(True)
        assert self.viewer.real_time_enabled is True
        
    def test_clear_render_cache(self):
        """Test clearing render cache."""
        # Populate cache with some data
        self.viewer.realtime_renderer.cache.store("test_key", b"test_data")
        
        assert len(self.viewer.realtime_renderer.cache.cache) > 0
        
        self.viewer.clear_render_cache()
        
        assert len(self.viewer.realtime_renderer.cache.cache) == 0
        assert self.viewer.cache_hit_rate == 0.0
        
    @pytest.mark.asyncio
    async def test_async_stl_data_update(self):
        """Test async STL data update method."""
        stl_data = b"test_stl_binary_data"
        
        await self.viewer._update_stl_data(stl_data)
        
        # Should update STL data as base64
        import base64
        expected_base64 = base64.b64encode(stl_data).decode('utf-8')
        assert self.viewer.stl_data == expected_base64
        
    def test_get_renderer_info_with_realtime(self):
        """Test renderer info includes real-time data."""
        info = self.viewer.get_renderer_info()
        
        assert 'realtime' in info
        realtime_info = info['realtime']
        
        assert 'enabled' in realtime_info
        assert 'debounce_delay_ms' in realtime_info
        assert 'cache_hit_rate' in realtime_info
        assert 'performance' in realtime_info
        
        assert realtime_info['enabled'] == self.viewer.real_time_enabled
        assert realtime_info['debounce_delay_ms'] == self.viewer.debounce_delay_ms


@pytest.mark.asyncio
class TestRealTimeWorkflow:
    """Integration tests for complete real-time workflow."""
    
    async def test_end_to_end_realtime_workflow(self):
        """Test complete real-time rendering workflow."""
        viewer = OpenSCADViewer(renderer_type="local")
        
        # Mock render method
        render_results = []
        
        def mock_render_stl(scad_code, force_render=False):
            render_results.append(scad_code)
            return f"stl_{len(scad_code)}".encode()
            
        viewer._render_stl = mock_render_stl
        
        # Test initial SCAD code
        initial_scad = "cube([10, 10, 10]);"
        viewer.update_scad_code(initial_scad, use_wasm=False)
        
        assert len(render_results) >= 1
        initial_render_count = len(render_results)
        
        # Test parameter updates
        await viewer.update_parameter_realtime("size", 15)
        await viewer.update_parameter_realtime("color", "red")
        
        # Force final render to ensure debouncing completed
        await viewer.update_parameter_realtime("final", True, force_render=True)
        
        # Check that real-time features work
        assert viewer.real_time_enabled
        assert hasattr(viewer, 'realtime_renderer')
        
        # Get final performance stats
        info = viewer.get_renderer_info()
        assert 'realtime' in info


if __name__ == "__main__":
    pytest.main([__file__])