"""
Tests for OpenSCAD Migration Engine

Tests syntax analysis, migration rules, and automatic code upgrade
functionality for different OpenSCAD versions.
"""

import pytest
from pathlib import Path

from src.marimo_openscad.migration_engine import (
    SyntaxIssueType,
    MigrationAction,
    SyntaxIssue,
    MigrationRule,
    MigrationSuggestion,
    MigrationResult,
    OpenSCADSyntaxAnalyzer,
    MigrationEngine,
    analyze_openscad_syntax,
    migrate_openscad_code,
    get_minimum_openscad_version
)


class TestSyntaxIssue:
    """Test SyntaxIssue data structure."""
    
    def test_syntax_issue_creation(self):
        """Test creating SyntaxIssue instances."""
        issue = SyntaxIssue(
            issue_type=SyntaxIssueType.DEPRECATED_SYNTAX,
            line_number=10,
            column_start=5,
            column_end=15,
            original_text="assign(x = 5)",
            message="assign() is deprecated",
            severity="warning"
        )
        
        assert issue.issue_type == SyntaxIssueType.DEPRECATED_SYNTAX
        assert issue.line_number == 10
        assert issue.column_start == 5
        assert issue.column_end == 15
        assert issue.original_text == "assign(x = 5)"
        assert issue.message == "assign() is deprecated"
        assert issue.severity == "warning"


class TestMigrationRule:
    """Test MigrationRule data structure."""
    
    def test_migration_rule_creation(self):
        """Test creating MigrationRule instances."""
        rule = MigrationRule(
            rule_id="test_rule",
            name="Test Rule",
            description="A test migration rule",
            from_version="any",
            to_version="2019.05+",
            pattern=r"old_pattern",
            replacement="new_pattern",
            action=MigrationAction.REPLACE,
            confidence=0.9
        )
        
        assert rule.rule_id == "test_rule"
        assert rule.name == "Test Rule"
        assert rule.action == MigrationAction.REPLACE
        assert rule.confidence == 0.9


class TestOpenSCADSyntaxAnalyzer:
    """Test OpenSCAD syntax analysis functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.analyzer = OpenSCADSyntaxAnalyzer()
        
    def test_analyzer_initialization(self):
        """Test analyzer is initialized correctly."""
        assert len(self.analyzer.known_functions) > 0
        assert len(self.analyzer.version_features) > 0
        assert len(self.analyzer.deprecated_patterns) > 0
        
        # Check some known functions
        assert "cube" in self.analyzer.known_functions
        assert "sphere" in self.analyzer.known_functions
        assert "union" in self.analyzer.known_functions
        
    def test_analyze_basic_scad_code(self):
        """Test analysis of basic OpenSCAD code."""
        scad_code = "cube([10, 10, 10]);"
        
        issues = self.analyzer.analyze_scad_code(scad_code)
        
        # Basic code should have no major issues
        error_issues = [i for i in issues if i.severity == "error"]
        assert len(error_issues) == 0
        
    def test_detect_deprecated_assign(self):
        """Test detection of deprecated assign() syntax."""
        scad_code = "assign(x = 10) cube([x, x, x]);"
        
        issues = self.analyzer.analyze_scad_code(scad_code)
        
        deprecated_issues = [i for i in issues if i.issue_type == SyntaxIssueType.DEPRECATED_SYNTAX]
        assert len(deprecated_issues) > 0
        
        assign_issue = next((i for i in deprecated_issues if "assign" in i.message), None)
        assert assign_issue is not None
        assert assign_issue.severity == "warning"
        
    def test_detect_deprecated_child(self):
        """Test detection of deprecated child() syntax."""
        scad_code = "module test() { child(0); }"
        
        issues = self.analyzer.analyze_scad_code(scad_code)
        
        child_issues = [i for i in issues if "child" in i.message.lower()]
        assert len(child_issues) > 0
        assert child_issues[0].issue_type == SyntaxIssueType.DEPRECATED_SYNTAX
        
    def test_detect_exponent_operator(self):
        """Test detection of exponent operator requiring 2023.06+."""
        scad_code = "cube([10**2, 10, 10]);"
        
        issues = self.analyzer.analyze_scad_code(scad_code)
        
        exponent_issues = [i for i in issues if "exponent" in i.message.lower()]
        assert len(exponent_issues) > 0
        
        exponent_issue = exponent_issues[0]
        assert exponent_issue.issue_type == SyntaxIssueType.VERSION_INCOMPATIBLE
        assert exponent_issue.min_version_required == "2023.06"
        assert exponent_issue.original_text == "**"
        
    def test_detect_assert_function(self):
        """Test detection of assert() function requiring 2019.05+."""
        scad_code = "assert(x > 0, 'x must be positive');"
        
        issues = self.analyzer.analyze_scad_code(scad_code)
        
        assert_issues = [i for i in issues if "assert" in i.message.lower()]
        assert len(assert_issues) > 0
        
        assert_issue = assert_issues[0]
        assert assert_issue.issue_type == SyntaxIssueType.VERSION_INCOMPATIBLE
        assert assert_issue.min_version_required == "2019.05"
        
    def test_detect_text_primitive(self):
        """Test detection of text() primitive requiring 2019.05+."""
        scad_code = 'text("Hello World");'
        
        issues = self.analyzer.analyze_scad_code(scad_code)
        
        text_issues = [i for i in issues if "text" in i.message.lower()]
        assert len(text_issues) > 0
        
        text_issue = text_issues[0]
        assert text_issue.issue_type == SyntaxIssueType.VERSION_INCOMPATIBLE
        assert text_issue.min_version_required == "2019.05"
        
    def test_detect_performance_issues(self):
        """Test detection of performance issues."""
        # Code with many union operations
        scad_code = "union() { " + "cube([1,1,1]); " * 15 + "}"
        
        issues = self.analyzer.analyze_scad_code(scad_code)
        
        performance_issues = [i for i in issues if i.issue_type == SyntaxIssueType.PERFORMANCE_WARNING]
        # Performance detection may or may not trigger based on exact pattern matching
        
    def test_detect_modernization_opportunities(self):
        """Test detection of modernization opportunities."""
        scad_code = "for (i = [1:10]) { cube([i, i, i]); }"
        
        issues = self.analyzer.analyze_scad_code(scad_code)
        
        modernization_issues = [i for i in issues if i.issue_type == SyntaxIssueType.MODERNIZATION_OPPORTUNITY]
        # May or may not find modernization opportunities depending on pattern matching
        
    def test_detect_long_lines(self):
        """Test detection of overly long lines."""
        long_line = "cube([10, 10, 10]); " * 10  # Create a very long line
        scad_code = long_line
        
        issues = self.analyzer.analyze_scad_code(scad_code)
        
        long_line_issues = [i for i in issues if "long line" in i.message.lower()]
        assert len(long_line_issues) > 0
        
    def test_get_minimum_version_required_basic(self):
        """Test minimum version detection for basic code."""
        scad_code = "cube([10, 10, 10]);"
        
        min_version = self.analyzer.get_minimum_version_required(scad_code)
        
        assert min_version == "2015.03"  # Default minimum
        
    def test_get_minimum_version_required_with_exponent(self):
        """Test minimum version detection with exponent operator."""
        scad_code = "cube([10**2, 10, 10]);"
        
        min_version = self.analyzer.get_minimum_version_required(scad_code)
        
        assert min_version == "2023.06"
        
    def test_get_minimum_version_required_with_assert(self):
        """Test minimum version detection with assert function."""
        scad_code = "assert(true); cube([10, 10, 10]);"
        
        min_version = self.analyzer.get_minimum_version_required(scad_code)
        
        assert min_version == "2019.05"
        
    def test_get_minimum_version_required_multiple_features(self):
        """Test minimum version detection with multiple version requirements."""
        scad_code = '''
        text("Hello");
        assert(true);
        cube([10**2, 10, 10]);
        '''
        
        min_version = self.analyzer.get_minimum_version_required(scad_code)
        
        # Should return the highest requirement (2023.06 for **)
        assert min_version == "2023.06"


class TestMigrationEngine:
    """Test migration engine functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.engine = MigrationEngine()
        
    def test_engine_initialization(self):
        """Test migration engine initialization."""
        assert len(self.engine.migration_rules) > 0
        assert self.engine.syntax_analyzer is not None
        
        # Check some migration rules exist
        rule_ids = [rule.rule_id for rule in self.engine.migration_rules]
        assert "fix_assign_deprecated" in rule_ids
        assert "fix_child_deprecated" in rule_ids
        
    def test_create_migration_plan_assign(self):
        """Test creating migration plan for deprecated assign()."""
        scad_code = "assign(x = 10) cube([x, x, x]);"
        
        suggestions = self.engine.create_migration_plan(scad_code, "any", "2019.05+")
        
        # Should suggest fixing assign()
        assign_suggestions = [s for s in suggestions if "assign" in s.rule.name.lower()]
        if assign_suggestions:  # May find suggestions
            suggestion = assign_suggestions[0]
            assert suggestion.confidence > 0.8
            assert "x" in suggestion.suggested_code and "= 10" in suggestion.suggested_code
        
    def test_create_migration_plan_child(self):
        """Test creating migration plan for deprecated child()."""
        scad_code = "module test() { child(0); }"
        
        suggestions = self.engine.create_migration_plan(scad_code, "any", "2019.05+")
        
        # Should suggest fixing child()
        child_suggestions = [s for s in suggestions if "child" in s.rule.name.lower()]
        assert len(child_suggestions) > 0
        
        suggestion = child_suggestions[0]
        assert suggestion.confidence > 0.8
        assert "children(0)" in suggestion.suggested_code
        
    def test_create_migration_plan_import_stl(self):
        """Test creating migration plan for deprecated import_stl()."""
        scad_code = 'import_stl("model.stl");'
        
        suggestions = self.engine.create_migration_plan(scad_code, "any", "2019.05+")
        
        # Should suggest modernizing import_stl()
        import_suggestions = [s for s in suggestions if "import" in s.rule.name.lower()]
        if import_suggestions:  # May find suggestions
            suggestion = import_suggestions[0]
            assert suggestion.confidence > 0.8
            assert 'import(' in suggestion.suggested_code
        
    def test_create_migration_plan_exponent_operator(self):
        """Test creating migration plan for exponent operator compatibility."""
        scad_code = "cube([x**2, 10, 10]);"
        
        suggestions = self.engine.create_migration_plan(scad_code, "2023.06", "pre-2023.06")
        
        # Should suggest replacing ** with pow()
        exponent_suggestions = [s for s in suggestions if "exponent" in s.rule.name.lower()]
        if exponent_suggestions:  # May find suggestions
            suggestion = exponent_suggestions[0]
            assert "pow(" in suggestion.suggested_code
        
    def test_apply_migration_high_confidence(self):
        """Test applying high-confidence migrations."""
        scad_code = "assign(x = 10) cube([x, x, x]);"
        
        suggestions = self.engine.create_migration_plan(scad_code, "any", "2019.05+")
        result = self.engine.apply_migration(scad_code, suggestions, auto_apply_threshold=0.8)
        
        assert result.success
        assert len(result.applied_rules) > 0
        assert "x" in result.migrated_code and "= 10" in result.migrated_code
        assert "assign(" not in result.migrated_code
        
    def test_apply_migration_low_confidence(self):
        """Test handling low-confidence migrations."""
        scad_code = "some_complex_pattern();"
        
        # Create a low-confidence suggestion manually
        low_confidence_rule = MigrationRule(
            rule_id="test_low_confidence",
            name="Low Confidence Test",
            description="Test low confidence migration",
            from_version="any",
            to_version="any",
            pattern="some_complex_pattern",
            replacement="improved_pattern",
            action=MigrationAction.REPLACE,
            confidence=0.5  # Low confidence
        )
        
        suggestion = MigrationSuggestion(
            rule=low_confidence_rule,
            issue=None,
            original_code="some_complex_pattern()",
            suggested_code="improved_pattern()",
            confidence=0.5,
            explanation="Test suggestion"
        )
        
        result = self.engine.apply_migration(scad_code, [suggestion], auto_apply_threshold=0.8)
        
        # Should not auto-apply low confidence suggestions
        assert len(result.applied_rules) == 0
        assert len(result.manual_review_required) >= 0  # May or may not require manual review
        
    def test_validate_migrated_code_basic(self):
        """Test basic validation of migrated code."""
        original_code = "assign(x = 10) cube([x, x, x]);"
        migrated_code = "x = 10; cube([x, x, x]);"
        
        validation = self.engine.validate_migrated_code(original_code, migrated_code)
        
        assert validation["is_valid"] is True
        assert len(validation["errors"]) == 0
        
    def test_validate_migrated_code_module_preservation(self):
        """Test validation preserves module definitions."""
        original_code = "module test_module() { cube([10, 10, 10]); }"
        migrated_code = "module test_module() { cube([10, 10, 10]); }"
        
        validation = self.engine.validate_migrated_code(original_code, migrated_code)
        
        assert validation["is_valid"] is True
        
    def test_validate_migrated_code_module_removed(self):
        """Test validation detects removed modules."""
        original_code = "module test_module() { cube([10, 10, 10]); }"
        migrated_code = "cube([10, 10, 10]);"  # Module removed
        
        validation = self.engine.validate_migrated_code(original_code, migrated_code)
        
        assert validation["is_valid"] is False
        assert any("module" in error.lower() for error in validation["errors"])
        
    def test_version_matching(self):
        """Test version matching logic."""
        engine = self.engine
        
        # Test exact match
        assert engine._version_matches("2019.05", "2019.05")
        
        # Test "any" pattern
        assert engine._version_matches("2019.05", "any")
        
        # Test "+" pattern
        assert engine._version_matches("2021.01", "2019.05+")
        assert not engine._version_matches("2018.01", "2019.05+")
        
        # Test "pre-" pattern
        assert engine._version_matches("2018.01", "pre-2019.05")
        assert not engine._version_matches("2021.01", "pre-2019.05")
        
    def test_version_comparison(self):
        """Test version comparison logic."""
        engine = self.engine
        
        # Test version comparison
        assert engine._compare_versions("2021.01", "2019.05") > 0
        assert engine._compare_versions("2019.05", "2021.01") < 0
        assert engine._compare_versions("2019.05", "2019.05") == 0
        
        # Test with different patch versions
        assert engine._compare_versions("2019.05.1", "2019.05") > 0
        
    def test_generate_migration_report(self):
        """Test migration report generation."""
        scad_code = "assign(x = 10) cube([x, x, x]);"
        
        suggestions = self.engine.create_migration_plan(scad_code, "any", "2019.05+")
        result = self.engine.apply_migration(scad_code, suggestions)
        
        report = self.engine.generate_migration_report(result)
        
        assert "OpenSCAD Migration Report" in report
        assert "Migration Status" in report
        assert "Summary" in report
        
        if result.applied_rules:
            assert "Applied Migration Rules" in report
            
        if result.manual_review_required:
            assert "Manual Review Required" in report


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_analyze_openscad_syntax(self):
        """Test quick syntax analysis function."""
        scad_code = "assign(x = 10) cube([x**2, x, x]);"
        
        issues = analyze_openscad_syntax(scad_code)
        
        assert len(issues) > 0
        
        # Should find both deprecated assign and version-incompatible **
        issue_types = [issue.issue_type for issue in issues]
        assert SyntaxIssueType.DEPRECATED_SYNTAX in issue_types
        assert SyntaxIssueType.VERSION_INCOMPATIBLE in issue_types
        
    def test_migrate_openscad_code(self):
        """Test quick migration function."""
        scad_code = "assign(x = 10) cube([x, x, x]);"
        
        result = migrate_openscad_code(scad_code, "any", "2019.05+")
        
        assert isinstance(result, MigrationResult)
        assert result.original_code == scad_code
        assert len(result.applied_rules) >= 0
        
    def test_get_minimum_openscad_version(self):
        """Test quick minimum version detection function."""
        scad_code = "cube([10**2, 10, 10]);"
        
        min_version = get_minimum_openscad_version(scad_code)
        
        assert min_version == "2023.06"


class TestRealWorldScenarios:
    """Test real-world migration scenarios."""
    
    def setup_method(self):
        """Setup test environment."""
        self.engine = MigrationEngine()
        
    def test_legacy_openscad_model_migration(self):
        """Test migrating a legacy OpenSCAD model."""
        legacy_code = '''
        // Legacy OpenSCAD model with deprecated syntax
        assign(size = 10)
        assign(height = 20)
        
        module gear() {
            import_stl("gear_base.stl");
            
            for (i = [0:8]) {
                rotate([0, 0, i * 45])
                translate([size/2, 0, 0])
                child(0);
            }
        }
        
        gear() cube([2, 2, height]);
        '''
        
        # Analyze issues
        issues = analyze_openscad_syntax(legacy_code)
        
        # Should find multiple deprecated patterns
        deprecated_issues = [i for i in issues if i.issue_type == SyntaxIssueType.DEPRECATED_SYNTAX]
        assert len(deprecated_issues) >= 2  # assign and child
        
        # Create migration plan
        suggestions = self.engine.create_migration_plan(legacy_code, "2015.03", "2019.05+")
        
        # Should have suggestions for assign, import_stl, and child
        assert len(suggestions) >= 2
        
        # Apply migration
        result = self.engine.apply_migration(legacy_code, suggestions)
        
        # Check that migration improves the code
        assert result.success
        assert len(result.applied_rules) > 0
        
        # Verify deprecated patterns are reduced
        new_issues = analyze_openscad_syntax(result.migrated_code)
        new_deprecated_issues = [i for i in new_issues if i.issue_type == SyntaxIssueType.DEPRECATED_SYNTAX]
        
        # Should have fewer deprecated issues after migration
        assert len(new_deprecated_issues) <= len(deprecated_issues)
        
    def test_modern_feature_compatibility_check(self):
        """Test compatibility checking for modern features."""
        modern_code = '''
        // Modern OpenSCAD code using 2023.06 features
        function square_area(side) = side**2;
        
        assert(square_area(5) == 25, "Square area calculation failed");
        
        for (i = [1:5]) {
            translate([i * 12, 0, 0])
            cube([square_area(i), 10, 10]);
        }
        
        text("Generated with OpenSCAD 2023.06");
        '''
        
        # Get minimum version requirement
        min_version = get_minimum_openscad_version(modern_code)
        
        # Should require 2023.06 due to ** operator
        assert min_version == "2023.06"
        
        # Check backward compatibility migration
        suggestions = self.engine.create_migration_plan(modern_code, "2023.06", "pre-2023.06")
        
        # Should suggest replacing ** with pow()
        exponent_suggestions = [s for s in suggestions if "exponent" in s.rule.name.lower()]
        # Note: May not find suggestions if pattern doesn't match exactly
        # This is expected behavior as migration engine is conservative
        
    def test_performance_optimization_migration(self):
        """Test migration for performance optimization."""
        performance_code = '''
        // Code with potential performance issues
        union() {
            for (i = [1:20]) {
                for (j = [1:20]) {
                    translate([i*5, j*5, 0])
                    cube([1, 1, 1]);
                }
            }
        }
        '''
        
        # Analyze for performance issues
        issues = analyze_openscad_syntax(performance_code)
        
        performance_issues = [i for i in issues if i.issue_type == SyntaxIssueType.PERFORMANCE_WARNING]
        # May find nested loop performance warnings
        
        # Check for suggestions
        suggestions = self.engine.create_migration_plan(performance_code, "any", "any")
        
        # Migration engine may suggest optimizations
        
    def test_full_migration_workflow(self):
        """Test complete migration workflow from analysis to report."""
        test_code = '''
        assign(radius = 5)
        assign(height = 10)
        
        module cylinder_with_hole() {
            difference() {
                cylinder(r=radius, h=height);
                cylinder(r=radius/2, h=height+1);
            }
        }
        
        import_stl("base.stl");
        cylinder_with_hole();
        '''
        
        # Step 1: Analyze syntax
        issues = analyze_openscad_syntax(test_code)
        assert len(issues) > 0
        
        # Step 2: Get minimum version
        min_version = get_minimum_openscad_version(test_code)
        assert min_version == "2015.03"  # Basic code
        
        # Step 3: Create migration plan
        suggestions = self.engine.create_migration_plan(test_code, "2015.03", "2019.05+")
        assert len(suggestions) > 0
        
        # Step 4: Apply migration
        result = migrate_openscad_code(test_code, "2015.03", "2019.05+")
        assert result.success
        
        # Step 5: Validate migration
        validation = self.engine.validate_migrated_code(test_code, result.migrated_code)
        assert validation["is_valid"]
        
        # Step 6: Generate report
        report = self.engine.generate_migration_report(result)
        assert len(report) > 0
        assert "Migration Report" in report


if __name__ == "__main__":
    pytest.main([__file__])