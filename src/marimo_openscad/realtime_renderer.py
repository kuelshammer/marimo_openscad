"""
Real-time Rendering Pipeline for Phase 3.3b

Implements debounced parameter updates, STL caching, and performance optimization
for smooth real-time 3D model updates in marimo notebooks.
"""

import asyncio
import hashlib
import json
import time
import weakref
from collections import OrderedDict
from typing import Dict, Any, Optional, Callable, Awaitable
import logging

logger = logging.getLogger(__name__)


class ParameterDebouncer:
    """
    Debounces parameter changes to prevent excessive rendering during rapid updates.
    
    Collects parameter changes over a specified delay window and triggers
    rendering only when changes stabilize.
    """
    
    def __init__(self, delay_ms: int = 100):
        """
        Initialize parameter debouncer.
        
        Args:
            delay_ms: Delay in milliseconds before triggering render after last change
        """
        self.delay_ms = delay_ms
        self.pending_changes: Dict[str, Any] = {}
        self.render_timer: Optional[asyncio.Task] = None
        self.render_callback: Optional[Callable] = None
        self.last_change_time = 0.0
        
    def update_parameter(self, name: str, value: Any) -> None:
        """
        Update a parameter value and schedule a debounced render.
        
        Args:
            name: Parameter name
            value: New parameter value
        """
        self.pending_changes[name] = value
        self.last_change_time = time.time()
        self._schedule_render()
        
    def set_render_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        """Set the callback function to call when render should be triggered."""
        self.render_callback = callback
        
    def _schedule_render(self) -> None:
        """Schedule a render after the debounce delay."""
        # Cancel existing timer
        if self.render_timer and not self.render_timer.done():
            self.render_timer.cancel()
            
        # Schedule new render - handle case where no event loop is running
        try:
            self.render_timer = asyncio.create_task(self._delayed_render())
        except RuntimeError:
            # No event loop running - this is normal in sync contexts
            # The render will be handled when force_render is called or in async context
            self.render_timer = None
        
    async def _delayed_render(self) -> None:
        """Execute delayed render after debounce period."""
        try:
            # Wait for debounce delay
            await asyncio.sleep(self.delay_ms / 1000.0)
            
            # Check if more changes occurred during delay
            if time.time() - self.last_change_time < (self.delay_ms / 1000.0):
                # Reschedule if changes are still coming
                self._schedule_render()
                return
                
            # Execute render with current pending changes
            if self.render_callback and self.pending_changes:
                changes = self.pending_changes.copy()
                self.pending_changes.clear()
                
                logger.info(f"🎯 Triggering debounced render with {len(changes)} parameter changes")
                await self.render_callback()
                
        except asyncio.CancelledError:
            # Timer was cancelled, ignore
            pass
        except Exception as e:
            logger.error(f"❌ Error in debounced render: {e}")
            
    def force_render(self) -> None:
        """Force immediate render, bypassing debounce delay."""
        if self.render_timer and not self.render_timer.done():
            self.render_timer.cancel()
            
        if self.render_callback and self.pending_changes:
            try:
                # Try to create immediate task
                asyncio.create_task(self.render_callback())
            except RuntimeError:
                # No event loop running - store for later execution
                logger.debug("No event loop for immediate render, storing pending changes")
            finally:
                self.pending_changes.clear()


class STLCache:
    """
    LRU cache for STL rendering results to avoid redundant computations.
    
    Caches STL data based on SCAD code and parameter combinations,
    with memory management and automatic cleanup.
    """
    
    def __init__(self, max_size_mb: int = 256, max_entries: int = 100):
        """
        Initialize STL cache.
        
        Args:
            max_size_mb: Maximum cache size in megabytes
            max_entries: Maximum number of cache entries
        """
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.max_entries = max_entries
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.current_size = 0
        self.hits = 0
        self.misses = 0
        
    def get_cache_key(self, scad_code: str, parameters: Optional[Dict] = None) -> str:
        """
        Generate cache key from SCAD code and parameters.
        
        Args:
            scad_code: OpenSCAD source code
            parameters: Parameter dictionary
            
        Returns:
            Cache key as hex digest
        """
        # Normalize parameters for consistent hashing
        param_str = json.dumps(parameters or {}, sort_keys=True)
        content = f"{scad_code}|{param_str}"
        return hashlib.sha256(content.encode()).hexdigest()
        
    def get(self, cache_key: str) -> Optional[bytes]:
        """
        Retrieve STL data from cache.
        
        Args:
            cache_key: Cache key to lookup
            
        Returns:
            STL binary data if found, None otherwise
        """
        if cache_key in self.cache:
            # Move to end (most recently used)
            entry = self.cache.pop(cache_key)
            self.cache[cache_key] = entry
            
            # Update access time and hit count
            entry['last_access'] = time.time()
            entry['access_count'] += 1
            self.hits += 1
            
            logger.debug(f"🎯 Cache HIT for key {cache_key[:8]}... (size: {len(entry['stl_data'])} bytes)")
            return entry['stl_data']
            
        self.misses += 1
        logger.debug(f"❌ Cache MISS for key {cache_key[:8]}...")
        return None
        
    def store(self, cache_key: str, stl_data: bytes, metadata: Optional[Dict] = None) -> None:
        """
        Store STL data in cache.
        
        Args:
            cache_key: Cache key
            stl_data: STL binary data
            metadata: Optional metadata dictionary
        """
        data_size = len(stl_data)
        
        # Check if single entry exceeds max size
        if data_size > self.max_size:
            logger.warning(f"⚠️ STL data too large for cache: {data_size} bytes > {self.max_size} bytes")
            return
            
        # Make room if necessary
        self._make_room(data_size)
        
        # Store entry
        entry = {
            'stl_data': stl_data,
            'size': data_size,
            'created': time.time(),
            'last_access': time.time(),
            'access_count': 1,
            'metadata': metadata or {}
        }
        
        self.cache[cache_key] = entry
        self.current_size += data_size
        
        logger.info(f"💾 Cached STL data: {data_size} bytes (total cache: {self.current_size} bytes, {len(self.cache)} entries)")
        
    def _make_room(self, needed_size: int) -> None:
        """Make room in cache by evicting LRU entries."""
        target_size = self.max_size - needed_size
        
        while (self.current_size > target_size or len(self.cache) >= self.max_entries) and self.cache:
            # Remove least recently used (first item in OrderedDict)
            lru_key, lru_entry = self.cache.popitem(last=False)
            self.current_size -= lru_entry['size']
            
            logger.debug(f"🗑️ Evicted LRU cache entry: {lru_key[:8]}... ({lru_entry['size']} bytes)")
            
    async def get_or_render(self, cache_key: str, render_func: Callable[[], Awaitable[bytes]]) -> bytes:
        """
        Get cached STL data or render and cache new data.
        
        Args:
            cache_key: Cache key to lookup
            render_func: Async function to render STL if not cached
            
        Returns:
            STL binary data
        """
        # Try cache first
        cached_data = self.get(cache_key)
        if cached_data is not None:
            return cached_data
            
        # Render new data
        start_time = time.time()
        stl_data = await render_func()
        render_time = time.time() - start_time
        
        # Store in cache with render time metadata
        metadata = {
            'render_time': render_time,
            'render_timestamp': time.time()
        }
        self.store(cache_key, stl_data, metadata)
        
        return stl_data
        
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests) if total_requests > 0 else 0.0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'total_size_bytes': self.current_size,
            'total_size_mb': self.current_size / (1024 * 1024),
            'entry_count': len(self.cache),
            'max_entries': self.max_entries,
            'max_size_mb': self.max_size / (1024 * 1024)
        }
        
    def clear(self) -> None:
        """Clear all cache entries."""
        cleared_size = self.current_size
        cleared_count = len(self.cache)
        
        self.cache.clear()
        self.current_size = 0
        
        logger.info(f"🧹 Cache cleared: {cleared_count} entries, {cleared_size} bytes freed")


class RealTimeRenderer:
    """
    Main real-time rendering coordinator combining debouncing and caching.
    
    Provides smooth parameter updates with intelligent caching and
    performance optimization for interactive 3D modeling.
    """
    
    def __init__(self, viewer, cache_size_mb: int = 256, debounce_ms: int = 100):
        """
        Initialize real-time renderer.
        
        Args:
            viewer: OpenSCADViewer instance
            cache_size_mb: STL cache size in megabytes
            debounce_ms: Parameter change debounce delay in milliseconds
        """
        self.viewer = weakref.ref(viewer)  # Avoid circular reference
        self.cache = STLCache(max_size_mb=cache_size_mb)
        self.debouncer = ParameterDebouncer(delay_ms=debounce_ms)
        self.is_rendering = False
        self.render_queue_size = 0
        
        # Set debouncer callback
        self.debouncer.set_render_callback(self._debounced_render)
        
        # Performance tracking
        self.render_count = 0
        self.total_render_time = 0.0
        self.last_render_time = 0.0
        
    async def update_parameter(self, name: str, value: Any, force_render: bool = False) -> None:
        """
        Update a parameter and trigger debounced rendering.
        
        Args:
            name: Parameter name
            value: New parameter value  
            force_render: If True, bypass debouncing
        """
        logger.info(f"🎛️ Parameter update: {name} = {value}")
        
        if force_render:
            # Apply parameter immediately and render
            await self._apply_parameter(name, value)
            await self._render_now()
        else:
            # Use debouncing for smooth updates
            self.debouncer.update_parameter(name, value)
            
    async def render_scad_code(self, scad_code: str, parameters: Optional[Dict] = None, use_cache: bool = True) -> bytes:
        """
        Render SCAD code with optional caching.
        
        Args:
            scad_code: OpenSCAD source code
            parameters: Parameter dictionary
            use_cache: Whether to use STL caching
            
        Returns:
            STL binary data
        """
        if not use_cache:
            return await self._render_direct(scad_code)
            
        # Use cache
        cache_key = self.cache.get_cache_key(scad_code, parameters)
        return await self.cache.get_or_render(
            cache_key,
            lambda: self._render_direct(scad_code)
        )
        
    async def _debounced_render(self) -> None:
        """Handle debounced render callback."""
        if self.is_rendering:
            self.render_queue_size += 1
            logger.debug(f"⏳ Render in progress, queuing request (queue size: {self.render_queue_size})")
            return
            
        await self._render_now()
        
        # Process any queued renders
        while self.render_queue_size > 0:
            self.render_queue_size -= 1
            await self._render_now()
            
    async def _render_now(self) -> None:
        """Execute immediate render."""
        viewer = self.viewer()
        if not viewer:
            logger.warning("⚠️ Viewer reference lost, cannot render")
            return
            
        self.is_rendering = True
        start_time = time.time()
        
        try:
            # Get current SCAD code
            scad_code = getattr(viewer, 'scad_code', '')
            if not scad_code:
                logger.warning("⚠️ No SCAD code available for rendering")
                return
                
            # Render with caching
            stl_data = await self.render_scad_code(scad_code)
            
            # Update viewer
            if hasattr(viewer, '_update_stl_data'):
                await viewer._update_stl_data(stl_data)
            else:
                # Fallback: use synchronous update
                import base64
                viewer.stl_data = base64.b64encode(stl_data).decode('utf-8')
                
            # Update performance metrics
            render_time = time.time() - start_time
            self.render_count += 1
            self.total_render_time += render_time
            self.last_render_time = render_time
            
            logger.info(f"✅ Real-time render complete: {render_time:.3f}s (avg: {self.get_avg_render_time():.3f}s)")
            
        except Exception as e:
            logger.error(f"❌ Real-time render failed: {e}")
        finally:
            self.is_rendering = False
            
    async def _render_direct(self, scad_code: str) -> bytes:
        """Direct STL rendering without caching."""
        viewer = self.viewer()
        if not viewer:
            raise RuntimeError("Viewer reference lost")
            
        # Use viewer's render method
        if hasattr(viewer, '_render_stl'):
            return viewer._render_stl(scad_code, force_render=True)
        else:
            raise RuntimeError("Viewer does not support direct STL rendering")
            
    async def _apply_parameter(self, name: str, value: Any) -> None:
        """Apply parameter change to current model."""
        # This would typically update the SCAD code with new parameter values
        # Implementation depends on parameter binding system
        pass
        
    def get_avg_render_time(self) -> float:
        """Get average render time."""
        if self.render_count == 0:
            return 0.0
        return self.total_render_time / self.render_count
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        cache_stats = self.cache.get_stats()
        
        return {
            'rendering': {
                'total_renders': self.render_count,
                'avg_render_time': self.get_avg_render_time(),
                'last_render_time': self.last_render_time,
                'is_rendering': self.is_rendering,
                'queue_size': self.render_queue_size
            },
            'cache': cache_stats,
            'debouncing': {
                'delay_ms': self.debouncer.delay_ms,
                'pending_changes': len(self.debouncer.pending_changes),
                'timer_active': self.debouncer.render_timer is not None and not self.debouncer.render_timer.done()
            }
        }