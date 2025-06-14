"""
Tests for Community Model Testing System

Tests the downloading, analysis, and compatibility testing of community
OpenSCAD models across different versions.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import hashlib

from src.marimo_openscad.community_model_tester import (
    CommunityModel,
    ModelTestResult,
    TestSuite,
    CommunityModelRegistry,
    ModelDownloader,
    CommunityModelTester,
    create_compatibility_test_suite
)
from src.marimo_openscad.migration_engine import SyntaxIssueType, SyntaxIssue


class TestCommunityModel:
    """Test CommunityModel data structure."""
    
    def test_community_model_creation(self):
        """Test creating CommunityModel instances."""
        model = CommunityModel(
            name="Test Model",
            source_url="https://example.com/model",
            description="A test model",
            author="test_author",
            license="MIT",
            tags=["test", "example"],
            file_size=1024,
            download_url="https://example.com/download/model.scad",
            popularity_score=75
        )
        
        assert model.name == "Test Model"
        assert model.author == "test_author"
        assert model.license == "MIT"
        assert "test" in model.tags
        assert model.file_size == 1024
        assert model.popularity_score == 75
        assert model.local_path is None  # Not downloaded yet


class TestModelTestResult:
    """Test ModelTestResult data structure."""
    
    def test_model_test_result_creation(self):
        """Test creating ModelTestResult instances."""
        model = CommunityModel(
            name="Test Model",
            source_url="https://example.com",
            description="Test",
            author="test",
            license="MIT",
            tags=["test"],
            file_size=1024,
            download_url="https://example.com/model.scad"
        )
        
        result = ModelTestResult(
            model=model,
            test_timestamp=datetime.now(),
            syntax_issues=[],
            minimum_version_required="2019.05",
            compatibility_score=0.85,
            test_status="passed"
        )
        
        assert result.model == model
        assert result.minimum_version_required == "2019.05"
        assert result.compatibility_score == 0.85
        assert result.test_status == "passed"
        assert result.notes == []  # Should initialize to empty list


class TestCommunityModelRegistry:
    """Test CommunityModelRegistry functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.registry = CommunityModelRegistry()
        
    def test_registry_initialization(self):
        """Test registry is initialized with models."""
        assert len(self.registry.models) > 0
        
        # Check that models have required fields
        for model in self.registry.models:
            assert model.name
            assert model.author
            assert model.download_url
            assert isinstance(model.tags, list)
            assert model.popularity_score >= 0
            
    def test_get_popular_models(self):
        """Test getting popular models."""
        popular = self.registry.get_popular_models(5)
        
        assert len(popular) <= 5
        assert len(popular) > 0
        
        # Should be sorted by popularity score (highest first)
        if len(popular) > 1:
            for i in range(len(popular) - 1):
                assert popular[i].popularity_score >= popular[i + 1].popularity_score
                
    def test_get_models_by_tag(self):
        """Test filtering models by tag."""
        # Test with a common tag
        mechanical_models = self.registry.get_models_by_tag("mechanical")
        
        for model in mechanical_models:
            assert any("mechanical" in tag.lower() for tag in model.tags)
            
        # Test with non-existent tag
        nonexistent = self.registry.get_models_by_tag("nonexistent_tag")
        assert len(nonexistent) == 0
        
    def test_get_model_by_name(self):
        """Test getting model by name."""
        # Get first model name
        if self.registry.models:
            first_model = self.registry.models[0]
            found_model = self.registry.get_model_by_name(first_model.name)
            
            assert found_model is not None
            assert found_model.name == first_model.name
            
        # Test non-existent model
        not_found = self.registry.get_model_by_name("Non-existent Model")
        assert not_found is None


class TestModelDownloader:
    """Test ModelDownloader functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.downloader = ModelDownloader(cache_dir=self.temp_dir)
        
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_downloader_initialization(self):
        """Test downloader initialization."""
        assert self.downloader.cache_dir == self.temp_dir
        assert self.downloader.cache_dir.exists()
        assert self.downloader.timeout_seconds == 30
        assert self.downloader.max_retries == 3
        
    def test_validate_scad_content_valid(self):
        """Test validation of valid OpenSCAD content."""
        valid_content = '''
        // Test OpenSCAD model
        module test_module() {
            cube([10, 10, 10]);
        }
        
        union() {
            translate([0, 0, 0]) sphere(5);
            rotate([0, 90, 0]) cylinder(r=2, h=10);
        }
        '''
        
        is_valid = self.downloader._validate_scad_content(valid_content)
        assert is_valid is True
        
    def test_validate_scad_content_invalid(self):
        """Test validation of invalid content."""
        # Too short
        short_content = "hello"
        assert self.downloader._validate_scad_content(short_content) is False
        
        # No OpenSCAD indicators
        non_scad_content = '''
        This is just plain text without any OpenSCAD constructs.
        It has multiple lines but no cube, sphere, module, etc.
        '''
        assert self.downloader._validate_scad_content(non_scad_content) is False
        
    @pytest.mark.asyncio
    async def test_download_model_success(self):
        """Test successful model download."""
        # Create mock model
        test_model = CommunityModel(
            name="Test Model",
            source_url="https://example.com",
            description="Test",
            author="test",
            license="MIT",
            tags=["test"],
            file_size=1024,
            download_url="https://example.com/model.scad"
        )
        
        # Mock successful HTTP response
        mock_content = '''
        module test_gear() {
            cube([10, 10, 10]);
            sphere(5);
        }
        '''
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status = Mock()
            mock_response.text = AsyncMock(return_value=mock_content)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            success = await self.downloader.download_model(test_model)
            
            assert success is True
            assert test_model.local_path is not None
            assert test_model.local_path.exists()
            assert test_model.checksum is not None
            
            # Verify content was saved correctly
            saved_content = test_model.local_path.read_text()
            assert saved_content == mock_content
            
    @pytest.mark.asyncio
    async def test_download_model_already_cached(self):
        """Test download when model is already cached."""
        test_model = CommunityModel(
            name="Cached Model",
            source_url="https://example.com",
            description="Test",
            author="test",
            license="MIT",
            tags=["test"],
            file_size=1024,
            download_url="https://example.com/cached.scad"
        )
        
        # Pre-create cached file
        url_hash = hashlib.md5(test_model.download_url.encode()).hexdigest()
        safe_name = "".join(c for c in test_model.name if c.isalnum() or c in "._- ")
        cache_filename = f"{safe_name}_{url_hash}.scad"
        cache_path = self.temp_dir / cache_filename
        cache_path.write_text("module cached() { cube([1,1,1]); }")
        
        success = await self.downloader.download_model(test_model)
        
        assert success is True
        assert test_model.local_path == cache_path
        
    @pytest.mark.asyncio  
    async def test_download_model_http_error(self):
        """Test download failure due to HTTP error."""
        test_model = CommunityModel(
            name="Error Model",
            source_url="https://example.com",
            description="Test",
            author="test",
            license="MIT",
            tags=["test"],
            file_size=1024,
            download_url="https://example.com/error.scad"
        )
        
        # Mock HTTP error
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            success = await self.downloader.download_model(test_model)
            
            assert success is False
            assert test_model.local_path is None
            
    @pytest.mark.asyncio
    async def test_download_models_multiple(self):
        """Test downloading multiple models."""
        models = [
            CommunityModel(
                name=f"Model {i}",
                source_url="https://example.com",
                description="Test",
                author="test",
                license="MIT",
                tags=["test"],
                file_size=1024,
                download_url=f"https://example.com/model{i}.scad"
            )
            for i in range(3)
        ]
        
        # Mock successful downloads
        with patch.object(self.downloader, 'download_model', return_value=True) as mock_download:
            successful = await self.downloader.download_models(models)
            
            assert len(successful) == 3
            assert mock_download.call_count == 3
            
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        # Create some test files
        test_files = []
        for i in range(3):
            test_file = self.temp_dir / f"test_model_{i}.scad"
            test_file.write_text(f"// Test model {i}")
            test_files.append(test_file)
        
        # Clear all
        cleared_count = self.downloader.clear_cache()
        
        assert cleared_count == 3
        for test_file in test_files:
            assert not test_file.exists()


class TestCommunityModelTester:
    """Test CommunityModelTester functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.tester = CommunityModelTester(cache_dir=self.temp_dir)
        
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_tester_initialization(self):
        """Test tester initialization."""
        assert self.tester.registry is not None
        assert self.tester.downloader is not None
        assert self.tester.syntax_analyzer is not None
        assert self.tester.migration_engine is not None
        assert len(self.tester.target_versions) > 0
        
    @pytest.mark.asyncio
    async def test_test_model_success(self):
        """Test successful model testing."""
        # Create test model with local file
        test_content = '''
        module test_gear(radius=5) {
            cylinder(r=radius, h=10);
            for (i = [0:8]) {
                rotate([0, 0, i * 40])
                translate([radius + 2, 0, 0])
                cube([1, 1, 10]);
            }
        }
        
        test_gear();
        '''
        
        model_file = self.temp_dir / "test_model.scad"
        model_file.write_text(test_content)
        
        test_model = CommunityModel(
            name="Test Gear",
            source_url="https://example.com",
            description="Test gear model",
            author="test",
            license="MIT",
            tags=["gear", "test"],
            file_size=len(test_content),
            download_url="https://example.com/test.scad",
            local_path=model_file
        )
        
        result = await self.tester.test_model(test_model)
        
        assert isinstance(result, ModelTestResult)
        assert result.model == test_model
        assert result.test_status in ["passed", "failed", "error"]
        assert result.minimum_version_required
        assert 0.0 <= result.compatibility_score <= 1.0
        
    @pytest.mark.asyncio
    async def test_test_model_with_issues(self):
        """Test model testing with syntax issues."""
        # Create model with deprecated syntax
        problematic_content = '''
        assign(x = 10)
        assign(y = 20)
        
        module problematic() {
            import_stl("model.stl");
            child(0);
        }
        
        cube([x**2, y, 10]);
        '''
        
        model_file = self.temp_dir / "problematic_model.scad"
        model_file.write_text(problematic_content)
        
        test_model = CommunityModel(
            name="Problematic Model",
            source_url="https://example.com",
            description="Model with issues",
            author="test",
            license="MIT",
            tags=["test"],
            file_size=len(problematic_content),
            download_url="https://example.com/problematic.scad",
            local_path=model_file
        )
        
        result = await self.tester.test_model(test_model)
        
        assert len(result.syntax_issues) > 0
        assert result.minimum_version_required == "2023.06"  # Due to ** operator
        
        # Should have issues for deprecated assign, import_stl, child, and ** operator
        issue_types = [issue.issue_type for issue in result.syntax_issues]
        assert SyntaxIssueType.DEPRECATED_SYNTAX in issue_types
        assert SyntaxIssueType.VERSION_INCOMPATIBLE in issue_types
        
    @pytest.mark.asyncio
    async def test_test_model_download_failure(self):
        """Test model testing with download failure."""
        test_model = CommunityModel(
            name="Failed Download",
            source_url="https://example.com",
            description="Model that fails to download",
            author="test",
            license="MIT",
            tags=["test"],
            file_size=1024,
            download_url="https://example.com/nonexistent.scad"
        )
        
        # Mock download failure
        with patch.object(self.tester.downloader, 'download_model', return_value=False):
            result = await self.tester.test_model(test_model)
            
            assert result.test_status == "error"
            assert "download" in result.error_message.lower()
            assert result.compatibility_score == 0.0
            
    def test_calculate_compatibility_score(self):
        """Test compatibility score calculation."""
        # Test with no issues
        score = self.tester._calculate_compatibility_score([], "2019.05", "2023.06")
        assert score == 1.0
        
        # Test with error issues
        error_issue = SyntaxIssue(
            issue_type=SyntaxIssueType.SYNTAX_ERROR,
            line_number=1,
            column_start=0,
            column_end=10,
            original_text="syntax error",
            message="Syntax error",
            severity="error"
        )
        
        score = self.tester._calculate_compatibility_score([error_issue], "2019.05", "2023.06")
        assert score == 0.7  # 1.0 - 0.3 for error
        
        # Test with version incompatibility
        score = self.tester._calculate_compatibility_score([], "2023.06", "2019.05")
        assert score == 0.5  # 1.0 - 0.5 for version incompatibility
        
    def test_compare_versions(self):
        """Test version comparison."""
        assert self.tester._compare_versions("2023.06", "2019.05") > 0
        assert self.tester._compare_versions("2019.05", "2023.06") < 0
        assert self.tester._compare_versions("2019.05", "2019.05") == 0
        
    @pytest.mark.asyncio
    async def test_test_popular_models(self):
        """Test testing popular models."""
        # Mock successful downloads and testing
        with patch.object(self.tester.downloader, 'download_models') as mock_download:
            # Create mock models with local paths
            mock_models = []
            for i in range(3):
                model_file = self.temp_dir / f"mock_model_{i}.scad"
                model_file.write_text(f"cube([{i+1}, {i+1}, {i+1}]);")
                
                model = CommunityModel(
                    name=f"Mock Model {i}",
                    source_url="https://example.com",
                    description="Mock",
                    author="test",
                    license="MIT",
                    tags=["test"],
                    file_size=100,
                    download_url=f"https://example.com/mock{i}.scad",
                    local_path=model_file
                )
                mock_models.append(model)
            
            mock_download.return_value = mock_models
            
            results = await self.tester.test_popular_models(limit=3)
            
            assert len(results) == 3
            for result in results:
                assert isinstance(result, ModelTestResult)
                assert result.test_status in ["passed", "failed", "error"]
                
    @pytest.mark.asyncio
    async def test_create_test_suite(self):
        """Test creating a test suite."""
        # Mock models and testing
        with patch.object(self.tester, 'test_model') as mock_test:
            mock_result = ModelTestResult(
                model=Mock(),
                test_timestamp=datetime.now(),
                syntax_issues=[],
                minimum_version_required="2019.05",
                compatibility_score=0.8,
                test_status="passed"
            )
            mock_test.return_value = mock_result
            
            suite = await self.tester.create_test_suite(
                name="Test Suite",
                description="Test description",
                model_selection="popular",
                limit=2
            )
            
            assert isinstance(suite, TestSuite)
            assert suite.name == "Test Suite"
            assert suite.description == "Test description"
            assert len(suite.models) <= 2
            assert suite.total_models > 0
            assert 0.0 <= suite.pass_rate <= 1.0
            
    def test_generate_test_report(self):
        """Test test report generation."""
        # Create mock test suite
        mock_model = CommunityModel(
            name="Test Model",
            source_url="https://example.com",
            description="Test",
            author="test_author",
            license="MIT",
            tags=["test", "gear"],
            file_size=1024,
            download_url="https://example.com/test.scad"
        )
        
        mock_result = ModelTestResult(
            model=mock_model,
            test_timestamp=datetime.now(),
            syntax_issues=[],
            minimum_version_required="2019.05",
            compatibility_score=0.85,
            test_status="passed",
            notes=["Test completed successfully"]
        )
        
        test_suite = TestSuite(
            name="Test Suite",
            description="Test description",
            models=[mock_model],
            target_versions=["2019.05", "2023.06"],
            test_results=[mock_result],
            created_date=datetime.now(),
            pass_rate=1.0,
            total_models=1,
            passed_models=1,
            failed_models=0
        )
        
        report = self.tester.generate_test_report(test_suite)
        
        assert "Community Model Test Report" in report
        assert "Test Suite" in report
        assert "Summary" in report
        assert "Version Compatibility Analysis" in report
        assert "Model Test Results" in report
        assert mock_model.name in report
        assert mock_model.author in report


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.mark.asyncio
    async def test_test_popular_models_function(self):
        """Test convenience function for testing popular models."""
        with patch('src.marimo_openscad.community_model_tester.CommunityModelTester') as mock_tester_class:
            mock_tester = Mock()
            mock_tester.test_popular_models = AsyncMock(return_value=[])
            mock_tester_class.return_value = mock_tester
            
            # Import here to avoid module-level async function issues
            from src.marimo_openscad.community_model_tester import test_popular_models
            results = await test_popular_models(limit=5)
            
            assert isinstance(results, list)
            mock_tester.test_popular_models.assert_called_once_with(5)
            
    @pytest.mark.asyncio
    async def test_create_compatibility_test_suite_function(self):
        """Test convenience function for creating test suite."""
        with patch('src.marimo_openscad.community_model_tester.CommunityModelTester') as mock_tester_class:
            mock_tester = Mock()
            mock_suite = TestSuite(
                name="Test",
                description="Test",
                models=[],
                target_versions=[],
                test_results=[],
                created_date=datetime.now(),
                pass_rate=0.0,
                total_models=0,
                passed_models=0,
                failed_models=0
            )
            mock_tester.create_test_suite = AsyncMock(return_value=mock_suite)
            mock_tester_class.return_value = mock_tester
            
            suite = await create_compatibility_test_suite()
            
            assert isinstance(suite, TestSuite)
            mock_tester.create_test_suite.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])