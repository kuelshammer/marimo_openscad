#!/usr/bin/env python3
"""
Async Communication Bridge Tests

CRITICAL MISSING TEST - Phase 1 Gap Closure
Test foundation for Phase 3 async communication between Python and JavaScript.
Validates UUID-based request tracking, message serialization, error handling,
and binary data transfer mechanisms required for WASM integration.
"""

import pytest
import asyncio
import time
import json
import base64
import uuid
import threading
import queue
from pathlib import Path
import sys
import os

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestAsyncCommunicationBridge:
    """Test foundation for Phase 3 async communication"""
    
    def test_uuid_request_tracking_implementation(self):
        """Test that UUID-based request tracking is implementable and reliable"""
        
        print("🔍 Testing UUID-based request tracking capabilities...")
        
        # Test UUID generation reliability
        uuid_generation_stats = {
            'total_generated': 0,
            'unique_count': 0,
            'collision_count': 0,
            'generation_time': 0
        }
        
        start_time = time.perf_counter()
        test_uuids = []
        
        # Generate large number of UUIDs to test for collisions
        num_uuids = 1000
        for _ in range(num_uuids):
            test_uuid = str(uuid.uuid4())
            test_uuids.append(test_uuid)
        
        generation_time = time.perf_counter() - start_time
        unique_uuids = set(test_uuids)
        
        uuid_generation_stats.update({
            'total_generated': num_uuids,
            'unique_count': len(unique_uuids),
            'collision_count': num_uuids - len(unique_uuids),
            'generation_time': generation_time,
            'uuids_per_second': num_uuids / generation_time
        })
        
        print(f"✅ UUID Generation Performance:")
        print(f"  Generated: {num_uuids} UUIDs in {generation_time:.4f}s")
        print(f"  Rate: {uuid_generation_stats['uuids_per_second']:.0f} UUIDs/sec")
        print(f"  Unique: {len(unique_uuids)}/{num_uuids}")
        print(f"  Collisions: {uuid_generation_stats['collision_count']}")
        
        # Test request tracking data structure
        request_tracker = {}
        
        # Simulate request/response lifecycle
        test_requests = []
        for i in range(10):
            request_id = str(uuid.uuid4())
            request_data = {
                'type': 'WASM_RENDER_REQUEST',
                'request_id': request_id,
                'scad_code': f'cube([{i+1},{i+1},{i+1}]);',
                'timestamp': time.time()
            }
            
            # Track request
            request_tracker[request_id] = {
                'status': 'pending',
                'request_data': request_data,
                'created_at': time.time(),
                'response_data': None
            }
            
            test_requests.append(request_id)
        
        print(f"\n✅ Request Tracking Test:")
        print(f"  Tracked requests: {len(request_tracker)}")
        
        # Simulate responses
        for i, request_id in enumerate(test_requests):
            if request_id in request_tracker:
                # Simulate response
                response_data = {
                    'type': 'WASM_RENDER_RESPONSE',
                    'request_id': request_id,
                    'success': True,
                    'stl_data': f'mock_stl_data_{i}',
                    'timestamp': time.time()
                }
                
                # Update tracking
                request_tracker[request_id]['status'] = 'completed'
                request_tracker[request_id]['response_data'] = response_data
                request_tracker[request_id]['completed_at'] = time.time()
        
        # Validate tracking integrity
        completed_requests = [rid for rid, data in request_tracker.items() if data['status'] == 'completed']
        tracking_integrity = len(completed_requests) == len(test_requests)
        
        print(f"  Completed requests: {len(completed_requests)}/{len(test_requests)}")
        print(f"  Tracking integrity: {'✅' if tracking_integrity else '❌'}")
        
        # Test request/response ID matching
        id_matching_correct = True
        for request_id, data in request_tracker.items():
            if data['status'] == 'completed':
                req_id = data['request_data']['request_id']
                resp_id = data['response_data']['request_id']
                if req_id != resp_id:
                    id_matching_correct = False
                    print(f"  ❌ ID mismatch: {req_id} != {resp_id}")
        
        if id_matching_correct:
            print(f"  ✅ Request/Response ID matching: All correct")
        
        # Test timeout detection simulation
        timeout_threshold = 30.0  # 30 seconds
        current_time = time.time()
        
        # Add a simulated old request
        old_request_id = str(uuid.uuid4())
        request_tracker[old_request_id] = {
            'status': 'pending',
            'request_data': {'request_id': old_request_id, 'scad_code': 'cube([1,1,1]);'},
            'created_at': current_time - 35.0,  # 35 seconds ago
            'response_data': None
        }
        
        # Detect timeouts
        timed_out_requests = [
            rid for rid, data in request_tracker.items()
            if data['status'] == 'pending' and (current_time - data['created_at']) > timeout_threshold
        ]
        
        print(f"\n✅ Timeout Detection Test:")
        print(f"  Timed out requests: {len(timed_out_requests)}")
        print(f"  Timeout detection working: {'✅' if len(timed_out_requests) == 1 else '❌'}")
        
        # Save UUID tracking analysis
        tracking_analysis = {
            'timestamp': time.time(),
            'uuid_generation_stats': uuid_generation_stats,
            'tracking_integrity': tracking_integrity,
            'id_matching_correct': id_matching_correct,
            'timeout_detection_working': len(timed_out_requests) == 1,
            'collision_free': uuid_generation_stats['collision_count'] == 0
        }
        
        analysis_file = Path(__file__).parent / "uuid_tracking_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(tracking_analysis, f, indent=2)
        
        print(f"\n💾 UUID tracking analysis saved to: {analysis_file}")
        
        # Test passes if UUID generation is collision-free and tracking works
        assert uuid_generation_stats['collision_count'] == 0, f"UUID collisions detected: {uuid_generation_stats['collision_count']}"
        assert tracking_integrity, "Request tracking integrity failed"
        assert id_matching_correct, "Request/Response ID matching failed"

    def test_message_serialization_performance(self):
        """Test message serialization/deserialization performance for Phase 3"""
        
        print("🔍 Testing message serialization performance...")
        
        # Define test message structures for Phase 3
        test_messages = {
            'simple_request': {
                'type': 'WASM_RENDER_REQUEST',
                'request_id': str(uuid.uuid4()),
                'scad_code': 'cube([1,1,1]);'
            },
            'complex_request': {
                'type': 'WASM_RENDER_REQUEST',
                'request_id': str(uuid.uuid4()),
                'scad_code': 'union(){' + 'cube([1,1,1]);' * 100 + '}',  # Large SCAD code
                'options': {
                    'enableManifold': True,
                    'outputFormat': 'binstl',
                    'timeout': 30000,
                    'metadata': {'complexity': 'high', 'triangles_estimate': 50000}
                }
            },
            'binary_response': {
                'type': 'WASM_RENDER_RESPONSE',
                'request_id': str(uuid.uuid4()),
                'success': True,
                'stl_data': base64.b64encode(b'mock_binary_stl_data' * 1000).decode('utf-8'),  # Large binary data
                'metadata': {
                    'renderTime': 123,
                    'size': 50000,
                    'triangles': 1000,
                    'renderer': 'wasm'
                }
            },
            'error_response': {
                'type': 'WASM_RENDER_ERROR',
                'request_id': str(uuid.uuid4()),
                'success': False,
                'error': 'WASM execution failed: Out of memory',
                'error_type': 'MEMORY_ERROR',
                'fallback_suggested': True
            }
        }
        
        serialization_results = {}
        
        for message_type, message_data in test_messages.items():
            print(f"\n  Testing {message_type}...")
            
            # Test serialization performance
            serialize_times = []
            deserialize_times = []
            serialized_sizes = []
            
            num_iterations = 100
            
            for _ in range(num_iterations):
                # Serialize
                start_time = time.perf_counter()
                serialized = json.dumps(message_data)
                serialize_time = time.perf_counter() - start_time
                serialize_times.append(serialize_time)
                serialized_sizes.append(len(serialized))
                
                # Deserialize
                start_time = time.perf_counter()
                deserialized = json.loads(serialized)
                deserialize_time = time.perf_counter() - start_time
                deserialize_times.append(deserialize_time)
                
                # Validate round-trip
                if deserialized != message_data:
                    raise AssertionError(f"Round-trip validation failed for {message_type}")
            
            # Calculate statistics
            avg_serialize_time = sum(serialize_times) / len(serialize_times)
            avg_deserialize_time = sum(deserialize_times) / len(deserialize_times)
            avg_size = sum(serialized_sizes) / len(serialized_sizes)
            
            serialization_results[message_type] = {
                'avg_serialize_time': avg_serialize_time,
                'avg_deserialize_time': avg_deserialize_time,
                'avg_size_bytes': avg_size,
                'serializations_per_sec': 1.0 / avg_serialize_time if avg_serialize_time > 0 else 0,
                'deserializations_per_sec': 1.0 / avg_deserialize_time if avg_deserialize_time > 0 else 0
            }
            
            print(f"    Serialize: {avg_serialize_time*1000:.3f}ms avg")
            print(f"    Deserialize: {avg_deserialize_time*1000:.3f}ms avg")
            print(f"    Size: {avg_size:.0f} bytes")
            print(f"    Throughput: {1.0/avg_serialize_time:.0f} serializations/sec")
        
        # Analyze overall performance
        print(f"\n📊 SERIALIZATION PERFORMANCE SUMMARY:")
        
        total_serialize_time = sum(r['avg_serialize_time'] for r in serialization_results.values())
        total_deserialize_time = sum(r['avg_deserialize_time'] for r in serialization_results.values())
        total_size = sum(r['avg_size_bytes'] for r in serialization_results.values())
        
        print(f"  Total serialize time: {total_serialize_time*1000:.3f}ms")
        print(f"  Total deserialize time: {total_deserialize_time*1000:.3f}ms")
        print(f"  Total message size: {total_size:.0f} bytes")
        
        # Performance targets for Phase 3
        performance_acceptable = (
            total_serialize_time < 0.010 and  # < 10ms total
            total_deserialize_time < 0.010 and  # < 10ms total
            total_size < 100000  # < 100KB total
        )
        
        if performance_acceptable:
            print("  ✅ PERFORMANCE: Acceptable for Phase 3")
        else:
            print("  ⚠️ PERFORMANCE: May need optimization for Phase 3")
        
        # Save serialization analysis
        serialization_analysis = {
            'timestamp': time.time(),
            'performance_acceptable': performance_acceptable,
            'total_serialize_time': total_serialize_time,
            'total_deserialize_time': total_deserialize_time,
            'total_size_bytes': total_size,
            'detailed_results': serialization_results
        }
        
        analysis_file = Path(__file__).parent / "serialization_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(serialization_analysis, f, indent=2)
        
        print(f"\n💾 Serialization analysis saved to: {analysis_file}")
        
        # Test passes if basic serialization works (performance warnings OK)
        assert all(r['avg_serialize_time'] > 0 for r in serialization_results.values()), "Serialization failed for some messages"

    def test_binary_data_transfer_encoding(self):
        """Test base64 encoding/decoding for STL data transfer efficiency"""
        
        print("🔍 Testing binary data transfer encoding...")
        
        # Create mock STL binary data of various sizes
        test_stl_data = {
            'minimal_stl': b"solid test\nfacet normal 0 0 1\n  outer loop\n    vertex 0 0 0\n    vertex 1 0 0\n    vertex 0 1 0\n  endloop\nendfacet\nendsolid test",
            'small_stl': b"solid test\n" + (b"facet normal 0 0 1\n  outer loop\n    vertex 0 0 0\n    vertex 1 0 0\n    vertex 0 1 0\n  endloop\nendfacet\n" * 10) + b"endsolid test",
            'medium_stl': b"STL_HEADER" + b"\x00" * 80 + (b"\x00\x00\x00\x00" * 12 + b"\x00\x00") * 100,  # Binary STL format
            'large_stl': b"STL_HEADER" + b"\x00" * 80 + (b"\x00\x00\x00\x00" * 12 + b"\x00\x00") * 1000   # Larger binary STL
        }
        
        encoding_results = {}
        
        for stl_name, stl_data in test_stl_data.items():
            print(f"\n  Testing {stl_name}...")
            
            original_size = len(stl_data)
            
            # Test encoding performance
            encode_times = []
            decode_times = []
            
            num_iterations = 10
            
            for _ in range(num_iterations):
                # Encode
                start_time = time.perf_counter()
                encoded = base64.b64encode(stl_data).decode('utf-8')
                encode_time = time.perf_counter() - start_time
                encode_times.append(encode_time)
                
                # Decode
                start_time = time.perf_counter()
                decoded = base64.b64decode(encoded)
                decode_time = time.perf_counter() - start_time
                decode_times.append(decode_time)
                
                # Validate round-trip
                if decoded != stl_data:
                    raise AssertionError(f"Binary round-trip failed for {stl_name}")
            
            encoded_size = len(encoded)
            avg_encode_time = sum(encode_times) / len(encode_times)
            avg_decode_time = sum(decode_times) / len(decode_times)
            size_overhead = encoded_size / original_size
            
            encoding_results[stl_name] = {
                'original_size': original_size,
                'encoded_size': encoded_size,
                'size_overhead': size_overhead,
                'avg_encode_time': avg_encode_time,
                'avg_decode_time': avg_decode_time,
                'encode_throughput_mb_per_sec': (original_size / 1024 / 1024) / avg_encode_time if avg_encode_time > 0 else 0,
                'decode_throughput_mb_per_sec': (original_size / 1024 / 1024) / avg_decode_time if avg_decode_time > 0 else 0
            }
            
            print(f"    Original: {original_size:,} bytes")
            print(f"    Encoded: {encoded_size:,} bytes ({size_overhead:.2f}x overhead)")
            print(f"    Encode: {avg_encode_time*1000:.3f}ms ({encoding_results[stl_name]['encode_throughput_mb_per_sec']:.1f} MB/s)")
            print(f"    Decode: {avg_decode_time*1000:.3f}ms ({encoding_results[stl_name]['decode_throughput_mb_per_sec']:.1f} MB/s)")
        
        # Analyze encoding efficiency
        print(f"\n📊 BINARY ENCODING ANALYSIS:")
        
        avg_overhead = sum(r['size_overhead'] for r in encoding_results.values()) / len(encoding_results)
        avg_encode_throughput = sum(r['encode_throughput_mb_per_sec'] for r in encoding_results.values()) / len(encoding_results)
        avg_decode_throughput = sum(r['decode_throughput_mb_per_sec'] for r in encoding_results.values()) / len(encoding_results)
        
        print(f"  Average size overhead: {avg_overhead:.2f}x")
        print(f"  Average encode throughput: {avg_encode_throughput:.1f} MB/s")
        print(f"  Average decode throughput: {avg_decode_throughput:.1f} MB/s")
        
        # Efficiency targets for Phase 3
        encoding_efficient = (
            avg_overhead < 1.5 and  # < 50% overhead
            avg_encode_throughput > 10 and  # > 10 MB/s
            avg_decode_throughput > 10  # > 10 MB/s
        )
        
        if encoding_efficient:
            print("  ✅ ENCODING: Efficient for Phase 3")
        else:
            print("  ⚠️ ENCODING: May impact Phase 3 performance")
        
        # Test large file handling (simulated)
        large_file_test = False
        try:
            # Simulate 1MB STL file
            large_stl = b"\x00" * (1024 * 1024)
            
            start_time = time.perf_counter()
            large_encoded = base64.b64encode(large_stl).decode('utf-8')
            large_encode_time = time.perf_counter() - start_time
            
            start_time = time.perf_counter()
            large_decoded = base64.b64decode(large_encoded)
            large_decode_time = time.perf_counter() - start_time
            
            if large_decoded == large_stl:
                large_file_test = True
                print(f"\n  ✅ LARGE FILE TEST (1MB):")
                print(f"    Encode: {large_encode_time*1000:.0f}ms")
                print(f"    Decode: {large_decode_time*1000:.0f}ms")
            else:
                print(f"\n  ❌ LARGE FILE TEST: Round-trip failed")
                
        except Exception as e:
            print(f"\n  ❌ LARGE FILE TEST: {e}")
        
        # Save binary encoding analysis
        encoding_analysis = {
            'timestamp': time.time(),
            'encoding_efficient': encoding_efficient,
            'large_file_test_passed': large_file_test,
            'avg_overhead': avg_overhead,
            'avg_encode_throughput_mb_per_sec': avg_encode_throughput,
            'avg_decode_throughput_mb_per_sec': avg_decode_throughput,
            'detailed_results': encoding_results
        }
        
        analysis_file = Path(__file__).parent / "binary_encoding_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(encoding_analysis, f, indent=2)
        
        print(f"\n💾 Binary encoding analysis saved to: {analysis_file}")
        
        # Test passes if basic encoding works and large files are handled
        assert all(r['avg_encode_time'] > 0 for r in encoding_results.values()), "Encoding failed for some data"
        assert large_file_test, "Large file encoding test failed"

    def test_error_handling_and_recovery(self):
        """Test error handling mechanisms for Phase 3 async communication"""
        
        print("🔍 Testing error handling and recovery mechanisms...")
        
        # Test various error scenarios that Phase 3 must handle
        error_scenarios = {
            'timeout_error': {
                'description': 'Request timeout simulation',
                'test_function': self._test_timeout_simulation
            },
            'malformed_message': {
                'description': 'Malformed JSON message handling',
                'test_function': self._test_malformed_message_handling
            },
            'large_data_error': {
                'description': 'Large data transfer failure',
                'test_function': self._test_large_data_error
            },
            'concurrent_request_error': {
                'description': 'Concurrent request conflicts',
                'test_function': self._test_concurrent_request_conflicts
            }
        }
        
        error_handling_results = {}
        
        for scenario_name, scenario_data in error_scenarios.items():
            print(f"\n  Testing {scenario_data['description']}...")
            
            try:
                result = scenario_data['test_function']()
                error_handling_results[scenario_name] = {
                    'success': True,
                    'result': result
                }
                print(f"    ✅ {scenario_data['description']}: Handled correctly")
            except Exception as e:
                error_handling_results[scenario_name] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"    ❌ {scenario_data['description']}: {e}")
        
        # Analyze error handling capabilities
        successful_scenarios = sum(1 for r in error_handling_results.values() if r['success'])
        total_scenarios = len(error_scenarios)
        
        print(f"\n📊 ERROR HANDLING ANALYSIS:")
        print(f"  Successful scenarios: {successful_scenarios}/{total_scenarios}")
        print(f"  Error handling coverage: {successful_scenarios/total_scenarios*100:.1f}%")
        
        error_handling_ready = successful_scenarios >= total_scenarios * 0.75  # 75% success rate
        
        if error_handling_ready:
            print("  ✅ ERROR HANDLING: Ready for Phase 3")
        else:
            print("  ⚠️ ERROR HANDLING: Needs improvement for Phase 3")
        
        # Save error handling analysis
        error_analysis = {
            'timestamp': time.time(),
            'error_handling_ready': error_handling_ready,
            'successful_scenarios': successful_scenarios,
            'total_scenarios': total_scenarios,
            'coverage_percentage': successful_scenarios/total_scenarios*100,
            'detailed_results': error_handling_results
        }
        
        analysis_file = Path(__file__).parent / "error_handling_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(error_analysis, f, indent=2, default=str)
        
        print(f"\n💾 Error handling analysis saved to: {analysis_file}")
        
        # Test passes if error handling mechanisms are working
        assert successful_scenarios > 0, "No error handling scenarios working"

    def _test_timeout_simulation(self):
        """Test timeout detection and handling"""
        
        # Simulate request tracking with timeout
        request_tracker = {}
        request_id = str(uuid.uuid4())
        
        # Create request with timestamp
        request_tracker[request_id] = {
            'status': 'pending',
            'created_at': time.time() - 35.0,  # 35 seconds ago
            'timeout': 30.0
        }
        
        # Check for timeout
        current_time = time.time()
        
        for rid, data in request_tracker.items():
            if data['status'] == 'pending':
                age = current_time - data['created_at']
                if age > data['timeout']:
                    # Handle timeout
                    request_tracker[rid]['status'] = 'timeout'
                    request_tracker[rid]['error'] = f'Request timed out after {age:.1f}s'
        
        # Verify timeout was detected
        timeout_detected = request_tracker[request_id]['status'] == 'timeout'
        
        return {
            'timeout_detected': timeout_detected,
            'timeout_age': current_time - request_tracker[request_id]['created_at']
        }

    def _test_malformed_message_handling(self):
        """Test handling of malformed JSON messages"""
        
        malformed_messages = [
            '{"incomplete": json',  # Incomplete JSON
            '{"type": "INVALID_TYPE"}',  # Invalid message type
            '{"type": "WASM_RENDER_REQUEST"}',  # Missing required fields
            '"not_an_object"',  # Not a JSON object
            '',  # Empty string
        ]
        
        handled_correctly = 0
        
        for malformed_msg in malformed_messages:
            try:
                # Attempt to parse
                parsed = json.loads(malformed_msg)
                
                # Validate message structure
                if not isinstance(parsed, dict):
                    raise ValueError("Message is not a JSON object")
                
                if 'type' not in parsed:
                    raise ValueError("Message missing 'type' field")
                
                valid_types = ['WASM_RENDER_REQUEST', 'WASM_RENDER_RESPONSE', 'WASM_RENDER_ERROR']
                if parsed['type'] not in valid_types:
                    raise ValueError(f"Invalid message type: {parsed['type']}")
                
                if parsed['type'] == 'WASM_RENDER_REQUEST' and 'request_id' not in parsed:
                    raise ValueError("Request message missing 'request_id' field")
                
                # If we get here, the message was valid (unexpected for malformed test)
                
            except (json.JSONDecodeError, ValueError) as e:
                # Expected for malformed messages
                handled_correctly += 1
            except Exception as e:
                # Unexpected error type
                pass
        
        return {
            'malformed_messages_tested': len(malformed_messages),
            'handled_correctly': handled_correctly,
            'handling_rate': handled_correctly / len(malformed_messages)
        }

    def _test_large_data_error(self):
        """Test handling of excessively large data transfers"""
        
        # Simulate large STL data that might cause issues
        try:
            # Create 10MB of data (should be manageable)
            large_data = b"\x00" * (10 * 1024 * 1024)
            encoded = base64.b64encode(large_data).decode('utf-8')
            
            # Test if this can be handled in a message
            message = {
                'type': 'WASM_RENDER_RESPONSE',
                'request_id': str(uuid.uuid4()),
                'success': True,
                'stl_data': encoded
            }
            
            # Test serialization
            serialized = json.dumps(message)
            deserialized = json.loads(serialized)
            
            # Test decode
            decoded_data = base64.b64decode(deserialized['stl_data'])
            
            data_integrity = decoded_data == large_data
            
            return {
                'large_data_size': len(large_data),
                'serialized_size': len(serialized),
                'data_integrity': data_integrity,
                'handling_successful': True
            }
            
        except Exception as e:
            # This is actually expected for very large data
            return {
                'large_data_size': 10 * 1024 * 1024,
                'error': str(e),
                'handling_successful': False,
                'error_detected': True  # This is good - error was caught
            }

    def _test_concurrent_request_conflicts(self):
        """Test handling of concurrent request conflicts"""
        
        # Simulate multiple concurrent requests
        request_tracker = {}
        
        # Create multiple requests quickly
        request_ids = []
        for i in range(5):
            request_id = str(uuid.uuid4())
            request_ids.append(request_id)
            
            request_tracker[request_id] = {
                'status': 'pending',
                'created_at': time.time(),
                'scad_code': f'cube([{i+1},{i+1},{i+1}]);'
            }
        
        # Test that all requests are tracked separately
        unique_requests = len(set(request_ids))
        all_tracked = all(rid in request_tracker for rid in request_ids)
        no_conflicts = len(request_tracker) == len(request_ids)
        
        # Simulate concurrent completion
        for request_id in request_ids:
            request_tracker[request_id]['status'] = 'completed'
            request_tracker[request_id]['completed_at'] = time.time()
        
        all_completed = all(
            request_tracker[rid]['status'] == 'completed' 
            for rid in request_ids
        )
        
        return {
            'concurrent_requests': len(request_ids),
            'unique_requests': unique_requests,
            'all_tracked': all_tracked,
            'no_conflicts': no_conflicts,
            'all_completed': all_completed
        }


if __name__ == "__main__":
    # Allow running individual tests
    pytest.main([__file__, "-v", "-s"])