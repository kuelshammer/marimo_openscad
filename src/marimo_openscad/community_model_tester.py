"""
Community Model Testing System

Downloads, analyzes, and tests popular OpenSCAD models from the community
to validate version compatibility and migration effectiveness.
"""

import os
import json
import asyncio
import aiohttp
import hashlib
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from urllib.parse import urlparse

from .migration_engine import (
    OpenSCADSyntaxAnalyzer, 
    MigrationEngine,
    SyntaxIssue,
    MigrationResult
)
from .version_manager import VersionInfo

logger = logging.getLogger(__name__)


@dataclass
class CommunityModel:
    """Information about a community OpenSCAD model."""
    name: str
    source_url: str
    description: str
    author: str
    license: str
    tags: List[str]
    file_size: int
    download_url: str
    local_path: Optional[Path] = None
    checksum: Optional[str] = None
    last_updated: Optional[datetime] = None
    popularity_score: int = 0  # Based on downloads, stars, etc.


@dataclass
class ModelTestResult:
    """Result of testing a community model."""
    model: CommunityModel
    test_timestamp: datetime
    syntax_issues: List[SyntaxIssue]
    minimum_version_required: str
    compatibility_score: float  # 0.0 to 1.0
    migration_result: Optional[MigrationResult] = None
    performance_metrics: Optional[Dict] = None
    test_status: str = "pending"  # "pending", "passed", "failed", "error"
    error_message: Optional[str] = None
    notes: List[str] = None
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []


@dataclass
class TestSuite:
    """A suite of community model tests."""
    name: str
    description: str
    models: List[CommunityModel]
    target_versions: List[str]
    test_results: List[ModelTestResult]
    created_date: datetime
    last_run: Optional[datetime] = None
    pass_rate: float = 0.0
    total_models: int = 0
    passed_models: int = 0
    failed_models: int = 0


class CommunityModelRegistry:
    """Registry of popular community OpenSCAD models."""
    
    def __init__(self):
        """Initialize the model registry."""
        self.models = self._load_popular_models()
    
    def _load_popular_models(self) -> List[CommunityModel]:
        """Load list of popular community models."""
        # In a real implementation, this would fetch from actual sources
        # For demo purposes, we'll use representative examples
        
        return [
            CommunityModel(
                name="Parametric Gear",
                source_url="https://github.com/chrisspen/openscad-models/blob/master/src/gear.scad",
                description="Parametric involute gear generator",
                author="chrisspen",
                license="GPL-3.0",
                tags=["gear", "mechanical", "parametric"],
                file_size=15420,
                download_url="https://raw.githubusercontent.com/chrisspen/openscad-models/master/src/gear.scad",
                popularity_score=95
            ),
            
            CommunityModel(
                name="Customizable Box",
                source_url="https://www.thingiverse.com/thing:1264391",
                description="Fully customizable box with various joint types",
                author="heartman",
                license="CC BY-SA 3.0",
                tags=["box", "container", "customizable"],
                file_size=8750,
                download_url="https://www.thingiverse.com/download:2071936",
                popularity_score=87
            ),
            
            CommunityModel(
                name="Spiral Vase",
                source_url="https://github.com/rcolyer/threads-scad",
                description="Spiral vase with customizable parameters",
                author="rcolyer",
                license="LGPL-2.1",
                tags=["vase", "spiral", "decorative"],
                file_size=6230,
                download_url="https://raw.githubusercontent.com/rcolyer/threads-scad/master/examples/spiral_vase.scad",
                popularity_score=72
            ),
            
            CommunityModel(
                name="Thread Library Demo",
                source_url="https://github.com/rcolyer/threads-scad",
                description="Demonstration of thread library functionality",
                author="rcolyer",
                license="LGPL-2.1",
                tags=["threads", "mechanical", "library"],
                file_size=12440,
                download_url="https://raw.githubusercontent.com/rcolyer/threads-scad/master/thread_test.scad",
                popularity_score=88
            ),
            
            CommunityModel(
                name="Advanced Text Module",
                source_url="https://github.com/thehans/text_on",
                description="Advanced text rendering with path following",
                author="thehans",
                license="MIT",
                tags=["text", "advanced", "rendering"],
                file_size=18990,
                download_url="https://raw.githubusercontent.com/thehans/text_on/master/text_on.scad",
                popularity_score=69
            ),
            
            CommunityModel(
                name="Bearing Generator",
                source_url="https://github.com/jbinvnt/openscad-bearing",
                description="Parametric ball bearing generator",
                author="jbinvnt",
                license="Apache-2.0",
                tags=["bearing", "mechanical", "parametric"],
                file_size=9870,
                download_url="https://raw.githubusercontent.com/jbinvnt/openscad-bearing/master/bearing.scad",
                popularity_score=81
            ),
            
            CommunityModel(
                name="Honeycomb Pattern",
                source_url="https://github.com/davidson16807/relativity.scad",
                description="Parametric honeycomb pattern generator",
                author="davidson16807",
                license="MIT",
                tags=["pattern", "honeycomb", "parametric"],
                file_size=7650,
                download_url="https://raw.githubusercontent.com/davidson16807/relativity.scad/master/honeycomb.scad",
                popularity_score=65
            ),
            
            CommunityModel(
                name="Celtic Knot Generator",
                source_url="https://github.com/beanz/celtic-knot-scad",
                description="Generates customizable Celtic knot patterns",
                author="beanz",
                license="GPL-3.0",
                tags=["celtic", "pattern", "decorative"],
                file_size=23450,
                download_url="https://raw.githubusercontent.com/beanz/celtic-knot-scad/master/celtic-knot.scad",
                popularity_score=58
            ),
            
            CommunityModel(
                name="Voronoi Diagram",
                source_url="https://github.com/JustinSDK/dotSCAD",
                description="Voronoi diagram implementation in OpenSCAD",
                author="JustinSDK",
                license="LGPL-3.0",
                tags=["voronoi", "mathematical", "algorithm"],
                file_size=16780,
                download_url="https://raw.githubusercontent.com/JustinSDK/dotSCAD/master/examples/voronoi2d.scad",
                popularity_score=73
            ),
            
            CommunityModel(
                name="Spring Generator",
                source_url="https://github.com/dpellegr/SpringSCAD",
                description="Parametric spring generator with various types",
                author="dpellegr",
                license="GPL-3.0",
                tags=["spring", "mechanical", "parametric"],
                file_size=11230,
                download_url="https://raw.githubusercontent.com/dpellegr/SpringSCAD/master/spring.scad",
                popularity_score=77
            )
        ]
    
    def get_popular_models(self, limit: int = 10) -> List[CommunityModel]:
        """Get most popular models."""
        sorted_models = sorted(self.models, key=lambda m: m.popularity_score, reverse=True)
        return sorted_models[:limit]
    
    def get_models_by_tag(self, tag: str) -> List[CommunityModel]:
        """Get models filtered by tag."""
        return [model for model in self.models if tag.lower() in [t.lower() for t in model.tags]]
    
    def get_model_by_name(self, name: str) -> Optional[CommunityModel]:
        """Get model by name."""
        for model in self.models:
            if model.name.lower() == name.lower():
                return model
        return None


class ModelDownloader:
    """Downloads community models for testing."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize model downloader.
        
        Args:
            cache_dir: Directory to cache downloaded models
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "marimo_openscad" / "community_models"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Download configuration
        self.timeout_seconds = 30
        self.max_retries = 3
        self.user_agent = "marimo-openscad/1.0 (Community Model Testing)"
    
    async def download_model(self, model: CommunityModel) -> bool:
        """
        Download a community model.
        
        Args:
            model: Model to download
            
        Returns:
            True if download was successful
        """
        try:
            # Generate cache filename
            url_hash = hashlib.md5(model.download_url.encode()).hexdigest()
            safe_name = "".join(c for c in model.name if c.isalnum() or c in "._- ")
            cache_filename = f"{safe_name}_{url_hash}.scad"
            cache_path = self.cache_dir / cache_filename
            
            # Check if already cached
            if cache_path.exists():
                logger.info(f"Model {model.name} already cached at {cache_path}")
                model.local_path = cache_path
                return True
            
            # Download model
            logger.info(f"Downloading model {model.name} from {model.download_url}")
            
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            headers = {"User-Agent": self.user_agent}
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(model.download_url) as response:
                    response.raise_for_status()
                    
                    content = await response.text()
                    
                    # Validate content is OpenSCAD code
                    if not self._validate_scad_content(content):
                        logger.warning(f"Downloaded content for {model.name} doesn't appear to be OpenSCAD code")
                        return False
                    
                    # Save to cache
                    cache_path.write_text(content, encoding='utf-8')
                    
                    # Calculate checksum
                    model.checksum = hashlib.sha256(content.encode()).hexdigest()
                    model.local_path = cache_path
                    
                    logger.info(f"Successfully downloaded {model.name} ({len(content)} characters)")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to download model {model.name}: {e}")
            return False
    
    def _validate_scad_content(self, content: str) -> bool:
        """Validate that content appears to be OpenSCAD code."""
        # Simple heuristic checks
        if len(content.strip()) < 10:
            return False
        
        # Check for common OpenSCAD patterns
        openscad_indicators = [
            "module ", "function ", "cube(", "sphere(", "cylinder(",
            "union(", "difference(", "intersection(",
            "translate(", "rotate(", "scale(",
            "//", "/*", "$", "echo("
        ]
        
        content_lower = content.lower()
        indicator_count = sum(1 for indicator in openscad_indicators if indicator in content_lower)
        
        # Should have at least a few OpenSCAD-specific constructs
        return indicator_count >= 3
    
    async def download_models(self, models: List[CommunityModel]) -> List[CommunityModel]:
        """
        Download multiple models concurrently.
        
        Args:
            models: List of models to download
            
        Returns:
            List of successfully downloaded models
        """
        download_tasks = [self.download_model(model) for model in models]
        results = await asyncio.gather(*download_tasks, return_exceptions=True)
        
        successful_models = []
        for model, result in zip(models, results):
            if isinstance(result, bool) and result:
                successful_models.append(model)
            elif isinstance(result, Exception):
                logger.error(f"Download failed for {model.name}: {result}")
        
        return successful_models
    
    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """Clear model cache."""
        cleared_count = 0
        cutoff_time = None
        
        if older_than_days:
            cutoff_time = datetime.now() - timedelta(days=older_than_days)
        
        for model_file in self.cache_dir.glob("*.scad"):
            should_clear = True
            
            if cutoff_time:
                file_time = datetime.fromtimestamp(model_file.stat().st_mtime)
                should_clear = file_time < cutoff_time
            
            if should_clear:
                try:
                    model_file.unlink()
                    cleared_count += 1
                    logger.info(f"Cleared cached model: {model_file}")
                except Exception as e:
                    logger.error(f"Failed to clear {model_file}: {e}")
        
        return cleared_count


class CommunityModelTester:
    """Tests community models for compatibility and issues."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize community model tester.
        
        Args:
            cache_dir: Directory for caching downloaded models
        """
        self.registry = CommunityModelRegistry()
        self.downloader = ModelDownloader(cache_dir)
        self.syntax_analyzer = OpenSCADSyntaxAnalyzer()
        self.migration_engine = MigrationEngine()
        
        # Test configuration
        self.target_versions = ["2015.03", "2019.05", "2021.01", "2022.03", "2023.06"]
        self.compatibility_threshold = 0.7  # Minimum score to consider compatible
    
    async def test_model(self, model: CommunityModel, 
                        target_version: str = "2023.06") -> ModelTestResult:
        """
        Test a single community model.
        
        Args:
            model: Model to test
            target_version: Target OpenSCAD version for compatibility
            
        Returns:
            Test result with compatibility information
        """
        try:
            # Ensure model is downloaded
            if not model.local_path or not model.local_path.exists():
                success = await self.downloader.download_model(model)
                if not success:
                    return ModelTestResult(
                        model=model,
                        test_timestamp=datetime.now(),
                        syntax_issues=[],
                        minimum_version_required="unknown",
                        compatibility_score=0.0,
                        test_status="error",
                        error_message="Failed to download model"
                    )
            
            # Read model content
            scad_content = model.local_path.read_text(encoding='utf-8')
            
            # Analyze syntax issues
            syntax_issues = self.syntax_analyzer.analyze_scad_code(scad_content)
            
            # Determine minimum version required
            min_version = self.syntax_analyzer.get_minimum_version_required(scad_content)
            
            # Calculate compatibility score
            compatibility_score = self._calculate_compatibility_score(
                syntax_issues, min_version, target_version
            )
            
            # Test migration if needed
            migration_result = None
            if min_version != target_version:
                try:
                    suggestions = self.migration_engine.create_migration_plan(
                        scad_content, min_version, target_version
                    )
                    migration_result = self.migration_engine.apply_migration(
                        scad_content, suggestions
                    )
                except Exception as e:
                    logger.warning(f"Migration failed for {model.name}: {e}")
            
            # Determine test status
            test_status = "passed" if compatibility_score >= self.compatibility_threshold else "failed"
            if compatibility_score == 0.0:
                test_status = "error"
            
            # Generate notes
            notes = []
            if syntax_issues:
                notes.append(f"Found {len(syntax_issues)} syntax issues")
            if migration_result and migration_result.success:
                notes.append(f"Migration successful: {len(migration_result.applied_rules)} rules applied")
            if min_version != "2015.03":
                notes.append(f"Requires OpenSCAD {min_version} or later")
            
            return ModelTestResult(
                model=model,
                test_timestamp=datetime.now(),
                syntax_issues=syntax_issues,
                minimum_version_required=min_version,
                compatibility_score=compatibility_score,
                migration_result=migration_result,
                test_status=test_status,
                notes=notes
            )
            
        except Exception as e:
            logger.error(f"Error testing model {model.name}: {e}")
            return ModelTestResult(
                model=model,
                test_timestamp=datetime.now(),
                syntax_issues=[],
                minimum_version_required="unknown",
                compatibility_score=0.0,
                test_status="error",
                error_message=str(e)
            )
    
    async def test_popular_models(self, limit: int = 10, 
                                 target_version: str = "2023.06") -> List[ModelTestResult]:
        """
        Test popular community models.
        
        Args:
            limit: Maximum number of models to test
            target_version: Target OpenSCAD version
            
        Returns:
            List of test results
        """
        popular_models = self.registry.get_popular_models(limit)
        
        # Download models first
        downloaded_models = await self.downloader.download_models(popular_models)
        
        # Test each model
        test_tasks = [
            self.test_model(model, target_version) 
            for model in downloaded_models
        ]
        
        results = await asyncio.gather(*test_tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, ModelTestResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Test task failed: {result}")
        
        return valid_results
    
    async def create_test_suite(self, name: str, description: str,
                               model_selection: str = "popular",
                               limit: int = 10) -> TestSuite:
        """
        Create a comprehensive test suite.
        
        Args:
            name: Test suite name
            description: Test suite description
            model_selection: "popular", "mechanical", "decorative", etc.
            limit: Maximum number of models to include
            
        Returns:
            Test suite with results
        """
        # Select models based on criteria
        if model_selection == "popular":
            models = self.registry.get_popular_models(limit)
        elif model_selection == "all":
            models = self.registry.models[:limit]
        else:
            # Filter by tag
            models = self.registry.get_models_by_tag(model_selection)[:limit]
        
        # Test all models across all target versions
        all_results = []
        
        for version in self.target_versions:
            version_results = await asyncio.gather(*[
                self.test_model(model, version) for model in models
            ], return_exceptions=True)
            
            # Filter valid results
            for result in version_results:
                if isinstance(result, ModelTestResult):
                    all_results.append(result)
        
        # Calculate suite statistics
        total_models = len(models) * len(self.target_versions)
        passed_models = len([r for r in all_results if r.test_status == "passed"])
        failed_models = len([r for r in all_results if r.test_status == "failed"])
        pass_rate = passed_models / total_models if total_models > 0 else 0.0
        
        return TestSuite(
            name=name,
            description=description,
            models=models,
            target_versions=self.target_versions,
            test_results=all_results,
            created_date=datetime.now(),
            last_run=datetime.now(),
            pass_rate=pass_rate,
            total_models=total_models,
            passed_models=passed_models,
            failed_models=failed_models
        )
    
    def _calculate_compatibility_score(self, syntax_issues: List[SyntaxIssue],
                                     min_version: str, target_version: str) -> float:
        """Calculate compatibility score based on issues and version requirements."""
        score = 1.0
        
        # Penalize based on syntax issues
        for issue in syntax_issues:
            if issue.severity == "error":
                score -= 0.3
            elif issue.severity == "warning":
                score -= 0.1
            elif issue.severity == "info":
                score -= 0.05
        
        # Penalize if minimum version is higher than target
        if self._compare_versions(min_version, target_version) > 0:
            score -= 0.5  # Significant penalty for version incompatibility
        
        return max(0.0, min(1.0, score))
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings."""
        try:
            parts1 = [int(x) for x in version1.split('.')]
            parts2 = [int(x) for x in version2.split('.')]
            
            # Pad to same length
            while len(parts1) < len(parts2):
                parts1.append(0)
            while len(parts2) < len(parts1):
                parts2.append(0)
            
            for p1, p2 in zip(parts1, parts2):
                if p1 < p2:
                    return -1
                elif p1 > p2:
                    return 1
            
            return 0
            
        except (ValueError, AttributeError):
            return 0
    
    def generate_test_report(self, test_suite: TestSuite) -> str:
        """Generate comprehensive test report."""
        report_lines = []
        
        report_lines.append(f"# Community Model Test Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Test Suite: {test_suite.name}")
        report_lines.append(f"Description: {test_suite.description}")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary statistics
        report_lines.append("## Summary")
        report_lines.append(f"- Total Tests: {test_suite.total_models}")
        report_lines.append(f"- Passed: {test_suite.passed_models}")
        report_lines.append(f"- Failed: {test_suite.failed_models}")
        report_lines.append(f"- Pass Rate: {test_suite.pass_rate:.1%}")
        report_lines.append(f"- Models Tested: {len(test_suite.models)}")
        report_lines.append(f"- Target Versions: {', '.join(test_suite.target_versions)}")
        report_lines.append("")
        
        # Version compatibility analysis
        report_lines.append("## Version Compatibility Analysis")
        
        for version in test_suite.target_versions:
            version_results = [r for r in test_suite.test_results 
                             if version in r.minimum_version_required or 
                             self._compare_versions(r.minimum_version_required, version) <= 0]
            
            if version_results:
                passed_count = len([r for r in version_results if r.test_status == "passed"])
                pass_rate = passed_count / len(version_results) if version_results else 0
                
                report_lines.append(f"### OpenSCAD {version}")
                report_lines.append(f"- Compatible Models: {passed_count}/{len(version_results)}")
                report_lines.append(f"- Compatibility Rate: {pass_rate:.1%}")
                report_lines.append("")
        
        # Model-specific results
        report_lines.append("## Model Test Results")
        
        # Group results by model
        model_results = {}
        for result in test_suite.test_results:
            model_name = result.model.name
            if model_name not in model_results:
                model_results[model_name] = []
            model_results[model_name].append(result)
        
        for model_name, results in model_results.items():
            report_lines.append(f"### {model_name}")
            
            # Get representative result (latest or best)
            best_result = max(results, key=lambda r: r.compatibility_score)
            
            report_lines.append(f"- Author: {best_result.model.author}")
            report_lines.append(f"- Tags: {', '.join(best_result.model.tags)}")
            report_lines.append(f"- Minimum Version: {best_result.minimum_version_required}")
            report_lines.append(f"- Compatibility Score: {best_result.compatibility_score:.2f}")
            report_lines.append(f"- Status: {best_result.test_status.upper()}")
            
            if best_result.syntax_issues:
                report_lines.append(f"- Syntax Issues: {len(best_result.syntax_issues)}")
                
                # Show critical issues
                critical_issues = [i for i in best_result.syntax_issues if i.severity == "error"]
                if critical_issues:
                    report_lines.append("  Critical Issues:")
                    for issue in critical_issues[:3]:  # Show first 3
                        report_lines.append(f"    - Line {issue.line_number}: {issue.message}")
            
            if best_result.migration_result and best_result.migration_result.success:
                report_lines.append(f"- Migration: {len(best_result.migration_result.applied_rules)} rules applied")
            
            if best_result.notes:
                report_lines.append(f"- Notes: {'; '.join(best_result.notes)}")
            
            report_lines.append("")
        
        # Common issues analysis
        all_issues = []
        for result in test_suite.test_results:
            all_issues.extend(result.syntax_issues)
        
        if all_issues:
            report_lines.append("## Common Issues Analysis")
            
            # Group issues by type and message
            issue_counts = {}
            for issue in all_issues:
                key = f"{issue.issue_type.value}: {issue.message}"
                issue_counts[key] = issue_counts.get(key, 0) + 1
            
            # Show most common issues
            sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
            
            report_lines.append("### Most Common Issues")
            for issue_desc, count in sorted_issues[:10]:
                report_lines.append(f"- {issue_desc} ({count} occurrences)")
            
            report_lines.append("")
        
        return "\n".join(report_lines)


# Convenience functions
async def test_popular_models(limit: int = 10) -> List[ModelTestResult]:
    """Quick test of popular community models."""
    tester = CommunityModelTester()
    return await tester.test_popular_models(limit)


async def create_compatibility_test_suite(name: str = "Community Compatibility") -> TestSuite:
    """Create standard compatibility test suite."""
    tester = CommunityModelTester()
    return await tester.create_test_suite(
        name=name,
        description="Standard community model compatibility testing",
        model_selection="popular",
        limit=10
    )