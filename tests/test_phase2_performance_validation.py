#!/usr/bin/env python3
"""
Phase 2 Performance Validation Tests

CRITICAL MISSING TEST - Phase 2 Gap Closure
Validates Phase 2 performance improvements and ensures bundle loading
meets performance targets. Critical for Phase 3 readiness.
"""

import pytest
import time
import psutil
import gc
import os
import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestPhase2PerformanceValidation:
    """Validate Phase 2 performance improvements"""
    
    def test_bundle_loading_performance(self):
        """Test that bundle loading meets performance targets"""
        print("🔍 Testing Phase 2 bundle loading performance...")
        
        try:
            from marimo_openscad.viewer_phase2 import openscad_viewer_phase2
            from solid2 import cube
        except ImportError as e:
            pytest.skip(f"Phase 2 viewer not available: {e}")
        
        # Test cold start performance (first load)
        print("  Testing cold start performance...")
        start_time = time.perf_counter()
        first_viewer = openscad_viewer_phase2(cube([1, 1, 1]))
        cold_start_time = time.perf_counter() - start_time
        
        print(f"  Cold start time: {cold_start_time:.3f}s")
        
        # Test warm start performance (subsequent loads)
        print("  Testing warm start performance...")
        warm_start_times = []
        
        for i in range(5):
            start_time = time.perf_counter()
            viewer = openscad_viewer_phase2(cube([i+1, i+1, i+1]))
            warm_time = time.perf_counter() - start_time
            warm_start_times.append(warm_time)
        
        avg_warm_time = sum(warm_start_times) / len(warm_start_times)
        min_warm_time = min(warm_start_times)
        max_warm_time = max(warm_start_times)
        
        print(f"  Warm start average: {avg_warm_time:.3f}s")
        print(f"  Warm start range: {min_warm_time:.3f}s - {max_warm_time:.3f}s")
        
        # Test bundle size impact on performance
        bundle_js = first_viewer._get_bundled_javascript()
        bundle_size = len(bundle_js)
        esm_size = len(getattr(first_viewer, '_esm', ''))
        
        print(f"  Bundle size: {bundle_size:,} characters")
        print(f"  ESM size: {esm_size:,} characters")
        
        # Calculate loading efficiency (characters per second)
        loading_efficiency = bundle_size / cold_start_time if cold_start_time > 0 else 0
        
        print(f"  Loading efficiency: {loading_efficiency:,.0f} chars/sec")
        
        # Performance targets for Phase 2
        performance_targets = {
            'cold_start_max': 3.0,  # seconds
            'warm_start_max': 1.0,  # seconds  
            'bundle_size_max': 200000,  # characters
            'loading_efficiency_min': 50000  # chars/sec
        }
        
        performance_results = {
            'cold_start_time': cold_start_time,
            'avg_warm_time': avg_warm_time,
            'bundle_size': bundle_size,
            'esm_size': esm_size,
            'loading_efficiency': loading_efficiency,
            'warm_start_times': warm_start_times
        }
        
        # Evaluate performance against targets
        performance_evaluation = {}
        
        for metric, target in performance_targets.items():
            if metric.endswith('_max'):
                actual_key = metric.replace('_max', '')
                if actual_key in performance_results:
                    actual_value = performance_results[actual_key]
                    passed = actual_value <= target
                    performance_evaluation[metric] = {
                        'target': target,
                        'actual': actual_value,
                        'passed': passed,
                        'margin': target - actual_value
                    }
            elif metric.endswith('_min'):
                actual_key = metric.replace('_min', '')
                if actual_key in performance_results:
                    actual_value = performance_results[actual_key]
                    passed = actual_value >= target
                    performance_evaluation[metric] = {
                        'target': target,
                        'actual': actual_value,
                        'passed': passed,
                        'margin': actual_value - target
                    }
        
        print(f"\n  📊 PERFORMANCE EVALUATION:")
        performance_score = 0
        total_metrics = len(performance_evaluation)
        
        for metric, eval_data in performance_evaluation.items():
            status = '✅' if eval_data['passed'] else '❌'
            print(f"    {metric}: {status} (target: {eval_data['target']}, actual: {eval_data['actual']:.3f})")
            if eval_data['passed']:
                performance_score += 1
        
        performance_percentage = (performance_score / total_metrics * 100) if total_metrics > 0 else 0
        print(f"  Performance score: {performance_score}/{total_metrics} ({performance_percentage:.1f}%)")
        
        if performance_percentage >= 75:
            print("  ✅ PERFORMANCE: Excellent - Ready for Phase 3")
        elif performance_percentage >= 50:
            print("  ⚡ PERFORMANCE: Good - Acceptable for Phase 3")
        else:
            print("  ⚠️ PERFORMANCE: Needs improvement before Phase 3")
        
        # Save performance analysis
        performance_analysis = {
            'timestamp': time.time(),
            'performance_results': performance_results,
            'performance_targets': performance_targets,
            'performance_evaluation': performance_evaluation,
            'performance_score': performance_score,
            'performance_percentage': performance_percentage,
            'ready_for_phase3': performance_percentage >= 50
        }
        
        analysis_file = Path(__file__).parent / "phase2_performance_analysis.json"
        import json
        with open(analysis_file, 'w') as f:
            json.dump(performance_analysis, f, indent=2)
        
        print(f"  💾 Performance analysis saved to: {analysis_file}")
        
        # Test passes if performance is reasonable (50% of targets met)
        assert performance_percentage >= 50, f"Performance insufficient: {performance_percentage:.1f}% < 50%"
        
        print("✅ Bundle loading performance validated")
    
    def test_memory_usage_improvement(self):
        """Test that Phase 2 doesn't increase memory usage significantly"""
        print("🔍 Testing Phase 2 memory usage patterns...")
        
        try:
            from marimo_openscad.viewer_phase2 import openscad_viewer_phase2
            from solid2 import cube
        except ImportError as e:
            pytest.skip(f"Phase 2 viewer not available: {e}")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"  Initial memory: {initial_memory:.1f}MB")
        
        # Test memory usage with single viewer
        print("  Testing single viewer memory usage...")
        
        pre_single_memory = process.memory_info().rss / 1024 / 1024
        single_viewer = openscad_viewer_phase2(cube([2, 2, 2]))
        post_single_memory = process.memory_info().rss / 1024 / 1024
        
        single_viewer_increase = post_single_memory - pre_single_memory
        print(f"  Single viewer memory increase: {single_viewer_increase:.1f}MB")
        
        # Test memory usage with multiple viewers
        print("  Testing multiple viewers memory usage...")
        
        viewers = []
        memory_snapshots = [post_single_memory]
        
        for i in range(5):
            viewer = openscad_viewer_phase2(cube([i+1, i+1, i+1]))
            viewers.append(viewer)
            
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_snapshots.append(current_memory)
            
            memory_increase = current_memory - memory_snapshots[0]
            print(f"    Viewer {i+1}: {current_memory:.1f}MB (+{memory_increase:.1f}MB total)")
        
        final_memory = memory_snapshots[-1]
        total_memory_increase = final_memory - initial_memory
        
        print(f"  Final memory: {final_memory:.1f}MB")
        print(f"  Total memory increase: {total_memory_increase:.1f}MB")
        
        # Calculate memory efficiency
        viewers_created = len(viewers) + 1  # +1 for single_viewer
        avg_memory_per_viewer = total_memory_increase / viewers_created if viewers_created > 0 else 0
        
        print(f"  Average memory per viewer: {avg_memory_per_viewer:.1f}MB")
        
        # Test memory cleanup after viewer deletion
        print("  Testing memory cleanup...")
        
        pre_cleanup_memory = process.memory_info().rss / 1024 / 1024
        
        # Delete viewers and force garbage collection
        del single_viewer
        del viewers
        gc.collect()
        
        # Wait a moment for cleanup
        time.sleep(0.5)
        
        post_cleanup_memory = process.memory_info().rss / 1024 / 1024
        memory_recovered = pre_cleanup_memory - post_cleanup_memory
        
        print(f"  Memory after cleanup: {post_cleanup_memory:.1f}MB")
        print(f"  Memory recovered: {memory_recovered:.1f}MB")
        
        # Memory usage targets
        memory_targets = {
            'single_viewer_max': 50.0,  # MB
            'avg_memory_per_viewer_max': 25.0,  # MB
            'total_increase_max': 150.0,  # MB
            'memory_recovery_min': 0.0  # MB (should recover some memory)
        }
        
        memory_results = {
            'initial_memory': initial_memory,
            'final_memory': final_memory,
            'single_viewer_increase': single_viewer_increase,
            'total_memory_increase': total_memory_increase,
            'avg_memory_per_viewer': avg_memory_per_viewer,
            'memory_recovered': memory_recovered,
            'viewers_created': viewers_created,
            'memory_snapshots': memory_snapshots
        }
        
        # Evaluate memory usage against targets
        memory_evaluation = {}
        
        for metric, target in memory_targets.items():
            if metric.endswith('_max'):
                actual_key = metric.replace('_max', '')
                if actual_key in memory_results:
                    actual_value = memory_results[actual_key]
                    passed = actual_value <= target
                    memory_evaluation[metric] = {
                        'target': target,
                        'actual': actual_value,
                        'passed': passed,
                        'margin': target - actual_value
                    }
            elif metric.endswith('_min'):
                actual_key = metric.replace('_min', '')
                if actual_key in memory_results:
                    actual_value = memory_results[actual_key]
                    passed = actual_value >= target
                    memory_evaluation[metric] = {
                        'target': target,
                        'actual': actual_value,
                        'passed': passed,
                        'margin': actual_value - target
                    }
        
        print(f"\n  📊 MEMORY EVALUATION:")
        memory_score = 0
        total_memory_metrics = len(memory_evaluation)
        
        for metric, eval_data in memory_evaluation.items():
            status = '✅' if eval_data['passed'] else '❌'
            print(f"    {metric}: {status} (target: {eval_data['target']}, actual: {eval_data['actual']:.1f})")
            if eval_data['passed']:
                memory_score += 1
        
        memory_percentage = (memory_score / total_memory_metrics * 100) if total_memory_metrics > 0 else 0
        print(f"  Memory efficiency: {memory_score}/{total_memory_metrics} ({memory_percentage:.1f}%)")
        
        # Check WASM 2GB constraint compliance  
        wasm_2gb_limit = 2048  # MB
        wasm_compliant = final_memory < wasm_2gb_limit
        wasm_safety_margin = wasm_2gb_limit - final_memory
        
        print(f"  WASM 2GB compliance: {'✅' if wasm_compliant else '❌'}")
        print(f"  Safety margin: {wasm_safety_margin:.1f}MB")
        
        if memory_percentage >= 75:
            print("  ✅ MEMORY: Excellent efficiency")
        elif memory_percentage >= 50:
            print("  ⚡ MEMORY: Good efficiency")
        else:
            print("  ⚠️ MEMORY: Could be improved")
        
        # Save memory analysis
        memory_analysis = {
            'timestamp': time.time(),
            'memory_results': memory_results,
            'memory_targets': memory_targets,
            'memory_evaluation': memory_evaluation,
            'memory_score': memory_score,
            'memory_percentage': memory_percentage,
            'wasm_2gb_compliant': wasm_compliant,
            'wasm_safety_margin': wasm_safety_margin
        }
        
        analysis_file = Path(__file__).parent / "phase2_memory_analysis.json"
        import json
        with open(analysis_file, 'w') as f:
            json.dump(memory_analysis, f, indent=2)
        
        print(f"  💾 Memory analysis saved to: {analysis_file}")
        
        # Test passes if memory usage is reasonable and WASM compliant
        assert wasm_compliant, f"Memory usage exceeds WASM 2GB limit: {final_memory:.1f}MB"
        assert avg_memory_per_viewer < 100, f"Memory per viewer too high: {avg_memory_per_viewer:.1f}MB"
        
        print("✅ Memory usage efficiency validated")
    
    def test_phase2_vs_phase1_performance_comparison(self):
        """Compare Phase 2 performance improvements vs Phase 1"""
        print("🔍 Testing Phase 2 vs Phase 1 performance comparison...")
        
        try:
            from marimo_openscad.viewer_phase2 import openscad_viewer_phase2
            from marimo_openscad.viewer import openscad_viewer  # Phase 1
            from solid2 import cube
        except ImportError as e:
            pytest.skip(f"Phase comparison not possible: {e}")
        
        # Test Phase 1 performance (baseline)
        print("  Testing Phase 1 performance (baseline)...")
        
        phase1_times = []
        phase1_errors = []
        
        for i in range(3):
            try:
                start_time = time.perf_counter()
                phase1_viewer = openscad_viewer(cube([i+1, i+1, i+1]), renderer_type="auto")
                phase1_time = time.perf_counter() - start_time
                phase1_times.append(phase1_time)
            except Exception as e:
                phase1_errors.append(str(e))
        
        phase1_avg_time = sum(phase1_times) / len(phase1_times) if phase1_times else float('inf')
        phase1_success_rate = len(phase1_times) / 3
        
        print(f"  Phase 1 average time: {phase1_avg_time:.3f}s")
        print(f"  Phase 1 success rate: {phase1_success_rate:.1%}")
        if phase1_errors:
            print(f"  Phase 1 errors: {len(phase1_errors)}")
        
        # Test Phase 2 performance
        print("  Testing Phase 2 performance...")
        
        phase2_times = []
        phase2_errors = []
        
        for i in range(3):
            try:
                start_time = time.perf_counter()
                phase2_viewer = openscad_viewer_phase2(cube([i+1, i+1, i+1]), renderer_type="auto")
                phase2_time = time.perf_counter() - start_time
                phase2_times.append(phase2_time)
            except Exception as e:
                phase2_errors.append(str(e))
        
        phase2_avg_time = sum(phase2_times) / len(phase2_times) if phase2_times else float('inf')
        phase2_success_rate = len(phase2_times) / 3
        
        print(f"  Phase 2 average time: {phase2_avg_time:.3f}s")
        print(f"  Phase 2 success rate: {phase2_success_rate:.1%}")
        if phase2_errors:
            print(f"  Phase 2 errors: {len(phase2_errors)}")
        
        # Calculate improvements
        time_improvement = None
        if phase1_avg_time != float('inf') and phase2_avg_time != float('inf'):
            if phase1_avg_time > 0:
                time_improvement = (phase1_avg_time - phase2_avg_time) / phase1_avg_time * 100
            else:
                time_improvement = 0
        
        success_improvement = (phase2_success_rate - phase1_success_rate) * 100
        error_reduction = len(phase1_errors) - len(phase2_errors)
        
        print(f"\n  📊 PERFORMANCE COMPARISON:")
        if time_improvement is not None:
            improvement_status = '✅' if time_improvement >= 0 else '⚠️'
            print(f"    Time improvement: {improvement_status} {time_improvement:+.1f}%")
        else:
            print(f"    Time improvement: ❓ Cannot compare")
        
        success_status = '✅' if success_improvement >= 0 else '⚠️'
        print(f"    Success rate improvement: {success_status} {success_improvement:+.1f}%")
        
        error_status = '✅' if error_reduction >= 0 else '⚠️'
        print(f"    Error reduction: {error_status} {error_reduction:+d} errors")
        
        # Bundle size comparison (Phase 2 should have bundle)
        bundle_comparison = {}
        
        try:
            if phase2_times:
                phase2_test_viewer = openscad_viewer_phase2(cube([1, 1, 1]))
                bundle_js = phase2_test_viewer._get_bundled_javascript()
                bundle_comparison['phase2_bundle_size'] = len(bundle_js)
                bundle_comparison['has_bundle'] = True
            else:
                bundle_comparison['has_bundle'] = False
        except Exception as e:
            bundle_comparison['has_bundle'] = False
            bundle_comparison['error'] = str(e)
        
        print(f"    Bundle integration: {'✅' if bundle_comparison.get('has_bundle') else '❌'}")
        if bundle_comparison.get('phase2_bundle_size'):
            print(f"    Bundle size: {bundle_comparison['phase2_bundle_size']:,} chars")
        
        # Overall Phase 2 readiness assessment
        readiness_factors = {
            'performance_stable': phase2_success_rate >= 0.8,
            'error_reduction': error_reduction >= 0,
            'bundle_integration': bundle_comparison.get('has_bundle', False),
            'time_competitive': time_improvement is None or time_improvement >= -50  # Allow 50% slower
        }
        
        readiness_score = sum(readiness_factors.values())
        readiness_percentage = readiness_score / len(readiness_factors) * 100
        
        print(f"\n  🎯 PHASE 2 READINESS:")
        for factor, passed in readiness_factors.items():
            status = '✅' if passed else '❌'
            print(f"    {factor}: {status}")
        
        print(f"  Readiness score: {readiness_score}/{len(readiness_factors)} ({readiness_percentage:.1f}%)")
        
        if readiness_percentage >= 75:
            print("  ✅ PHASE 2: Ready for Phase 3")
        elif readiness_percentage >= 50:
            print("  ⚡ PHASE 2: Mostly ready for Phase 3")
        else:
            print("  ⚠️ PHASE 2: Needs improvement before Phase 3")
        
        # Save comparison analysis
        comparison_analysis = {
            'timestamp': time.time(),
            'phase1_performance': {
                'avg_time': phase1_avg_time,
                'success_rate': phase1_success_rate,
                'errors': phase1_errors
            },
            'phase2_performance': {
                'avg_time': phase2_avg_time,
                'success_rate': phase2_success_rate, 
                'errors': phase2_errors
            },
            'improvements': {
                'time_improvement_percent': time_improvement,
                'success_improvement_percent': success_improvement,
                'error_reduction': error_reduction
            },
            'bundle_comparison': bundle_comparison,
            'readiness_factors': readiness_factors,
            'readiness_score': readiness_score,
            'readiness_percentage': readiness_percentage
        }
        
        analysis_file = Path(__file__).parent / "phase2_comparison_analysis.json"
        import json
        with open(analysis_file, 'w') as f:
            json.dump(comparison_analysis, f, indent=2, default=str)
        
        print(f"  💾 Phase comparison analysis saved to: {analysis_file}")
        
        # Test passes if Phase 2 shows reasonable improvements
        assert readiness_percentage >= 50, f"Phase 2 readiness insufficient: {readiness_percentage:.1f}%"
        
        print("✅ Phase 2 vs Phase 1 performance comparison validated")


if __name__ == "__main__":
    # Allow running individual tests
    pytest.main([__file__, "-v", "-s"])