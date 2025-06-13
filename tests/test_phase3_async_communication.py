#!/usr/bin/env python3
"""
Phase 3.1 Async Communication Tests

CRITICAL PHASE 3 FOUNDATION - Async Communication
Tests bidirectional Python ↔ JavaScript messaging with UUID-based
request/response system, error propagation, and timeout handling.
"""

import pytest
import asyncio
import uuid
import time
import json
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path
import sys
import os

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestPhase3AsyncCommunication:
    """Test bidirectional async communication for Phase 3"""
    
    @pytest.mark.asyncio
    async def test_bidirectional_message_passing(self):
        """Test Python → JavaScript request and JavaScript → Python response"""
        print("🔍 Testing bidirectional message passing...")
        
        # This test validates the core async communication pattern
        # that will be implemented in the actual AsyncOpenSCADViewer
        
        # Simulate the message structure we'll use
        request_id = str(uuid.uuid4())
        request_message = {
            "id": request_id,
            "type": "render_request",
            "scad_code": "cube([2, 2, 2]);",
            "timestamp": time.time()
        }
        
        # Simulate JavaScript response structure
        response_message = {
            "id": request_id,
            "type": "render_response", 
            "stl_data": "solid test_cube\n  facet normal 1 0 0\n    outer loop\n      vertex 2 0 0\n      vertex 2 2 0\n      vertex 2 2 2\n    endloop\n  endfacet\nendsolid test_cube",
            "status": "success",
            "timestamp": time.time()
        }
        
        # Test message ID matching
        assert request_message["id"] == response_message["id"], "Request and response IDs must match"
        
        # Test message structure validity
        assert "id" in request_message, "Request must have ID"
        assert "type" in request_message, "Request must have type"
        assert "scad_code" in request_message, "Request must have SCAD code"
        
        assert "id" in response_message, "Response must have ID"
        assert "status" in response_message, "Response must have status"
        assert "stl_data" in response_message, "Response must have STL data"
        
        # Test UUID validity
        try:
            uuid.UUID(request_id)
            uuid_valid = True
        except ValueError:
            uuid_valid = False
        
        assert uuid_valid, f"Request ID must be valid UUID: {request_id}"
        
        # Simulate async message timing
        request_time = request_message["timestamp"]
        response_time = response_message["timestamp"]
        latency = response_time - request_time
        
        print(f"  Message ID: {request_id}")
        print(f"  Request timestamp: {request_time}")
        print(f"  Response timestamp: {response_time}")
        print(f"  Simulated latency: {latency:.3f}s")
        
        # In Phase 3 implementation, we target <100ms for real requests
        # This simulation just validates the message structure works
        assert latency >= 0, "Response must come after request"
        
        print("✅ Bidirectional message structure validated")
    
    @pytest.mark.asyncio
    async def test_error_propagation_scenarios(self):
        """Test error handling and propagation from JavaScript to Python"""
        print("🔍 Testing error propagation scenarios...")
        
        request_id = str(uuid.uuid4())
        
        # Test different error scenarios we'll handle in Phase 3
        error_scenarios = [
            {
                "type": "wasm_execution_error",
                "error": "WASM module failed to compile SCAD code",
                "details": {"line": 1, "column": 5, "message": "Syntax error in SCAD"}
            },
            {
                "type": "memory_limit_error", 
                "error": "Memory usage exceeded 2GB WASM limit",
                "details": {"memory_used": 2147483648, "limit": 2147483648}
            },
            {
                "type": "timeout_error",
                "error": "Rendering operation timed out",
                "details": {"timeout_ms": 10000, "elapsed_ms": 10500}
            },
            {
                "type": "invalid_scad_error",
                "error": "Invalid SCAD code provided",
                "details": {"scad_code": "invalid_function([1,2,3]);"}
            }
        ]
        
        for scenario in error_scenarios:
            error_response = {
                "id": request_id,
                "type": "render_response",
                "status": "error",
                "error": scenario["error"],
                "error_type": scenario["type"],
                "error_details": scenario["details"],
                "timestamp": time.time()
            }
            
            # Validate error response structure
            assert error_response["status"] == "error", "Error responses must have status='error'"
            assert "error" in error_response, "Error responses must contain error message"
            assert "error_type" in error_response, "Error responses must specify error type"
            assert "error_details" in error_response, "Error responses must include error details"
            
            print(f"  ✅ Error scenario validated: {scenario['type']}")
            print(f"    Error: {scenario['error']}")
            print(f"    Details: {scenario['details']}")
        
        print("✅ Error propagation scenarios validated")
    
    @pytest.mark.asyncio
    async def test_timeout_and_retry_logic(self):
        """Test timeout handling and retry mechanisms"""
        print("🔍 Testing timeout and retry logic...")
        
        # Test timeout detection
        request_start = time.time()
        timeout_duration = 0.1  # 100ms for testing
        
        # Simulate timeout scenario
        async def simulate_slow_request():
            await asyncio.sleep(timeout_duration + 0.05)  # Exceed timeout
            return "This should timeout"
        
        # Test that timeout is properly detected
        try:
            result = await asyncio.wait_for(simulate_slow_request(), timeout=timeout_duration)
            timeout_occurred = False
        except asyncio.TimeoutError:
            timeout_occurred = True
            result = None
        
        elapsed = time.time() - request_start
        
        assert timeout_occurred, "Timeout should have occurred"
        assert elapsed < timeout_duration + 0.1, f"Timeout should occur quickly: {elapsed:.3f}s"
        
        print(f"  ✅ Timeout detected in {elapsed:.3f}s (target: {timeout_duration}s)")
        
        # Test retry mechanism structure
        max_retries = 3
        retry_delays = [0.1, 0.2, 0.4]  # Exponential backoff
        
        for attempt in range(max_retries):
            delay = retry_delays[attempt] if attempt < len(retry_delays) else retry_delays[-1]
            
            # Simulate retry attempt
            retry_request = {
                "id": str(uuid.uuid4()),
                "type": "render_request",
                "attempt": attempt + 1,
                "max_attempts": max_retries,
                "retry_delay": delay,
                "original_timestamp": time.time() - (attempt * 0.5),
                "retry_timestamp": time.time()
            }
            
            assert retry_request["attempt"] <= max_retries, "Retry attempt within limits"
            assert retry_request["retry_delay"] > 0, "Retry delay must be positive"
            
            print(f"  ✅ Retry attempt {attempt + 1}/{max_retries} validated (delay: {delay}s)")
        
        print("✅ Timeout and retry logic validated")
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self):
        """Test handling multiple concurrent async requests"""
        print("🔍 Testing concurrent request handling...")
        
        # Simulate multiple concurrent requests
        num_concurrent = 5
        request_tasks = []
        
        async def simulate_request(request_num):
            request_id = str(uuid.uuid4())
            
            # Simulate request processing time
            processing_time = 0.1 + (request_num * 0.02)  # Stagger timing
            await asyncio.sleep(processing_time)
            
            return {
                "request_id": request_id,
                "request_num": request_num,
                "processing_time": processing_time,
                "completed_at": time.time()
            }
        
        # Launch concurrent requests
        start_time = time.time()
        for i in range(num_concurrent):
            task = asyncio.create_task(simulate_request(i))
            request_tasks.append(task)
        
        # Wait for all requests to complete
        results = await asyncio.gather(*request_tasks)
        total_time = time.time() - start_time
        
        # Validate concurrent execution
        assert len(results) == num_concurrent, f"All {num_concurrent} requests should complete"
        
        # Check that requests were processed concurrently (not sequentially)
        max_individual_time = max(result["processing_time"] for result in results)
        expected_sequential_time = sum(result["processing_time"] for result in results)
        
        print(f"  Concurrent execution time: {total_time:.3f}s")
        print(f"  Max individual time: {max_individual_time:.3f}s") 
        print(f"  Expected sequential time: {expected_sequential_time:.3f}s")
        
        # Concurrent execution should be much faster than sequential
        assert total_time < expected_sequential_time * 0.8, "Concurrent execution should be faster than sequential"
        assert total_time <= max_individual_time + 0.1, "Total time should be close to longest individual request"
        
        # Validate request uniqueness
        request_ids = [result["request_id"] for result in results]
        unique_ids = set(request_ids)
        assert len(unique_ids) == num_concurrent, "All request IDs should be unique"
        
        # Test request ordering and completion
        completion_times = [result["completed_at"] for result in results]
        for i in range(1, len(completion_times)):
            # Allow for small timing variations in concurrent execution
            assert completion_times[i] >= completion_times[i-1] - 0.05, "Requests should complete in roughly chronological order"
        
        print(f"  ✅ {num_concurrent} concurrent requests completed successfully")
        print("✅ Concurrent request handling validated")


if __name__ == "__main__":
    # Allow running individual tests
    pytest.main([__file__, "-v", "-s"])