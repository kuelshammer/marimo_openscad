"""
OpenSCAD Migration & Upgrade Engine

Handles syntax analysis, version migration, and automatic code modernization
for OpenSCAD code across different versions.
"""

import re
import ast
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

from .version_manager import VersionInfo

logger = logging.getLogger(__name__)


class SyntaxIssueType(Enum):
    """Types of syntax issues that can be detected."""
    DEPRECATED_SYNTAX = "deprecated_syntax"
    VERSION_INCOMPATIBLE = "version_incompatible"
    PERFORMANCE_WARNING = "performance_warning"
    MODERNIZATION_OPPORTUNITY = "modernization_opportunity"
    SYNTAX_ERROR = "syntax_error"


class MigrationAction(Enum):
    """Types of migration actions that can be performed."""
    REPLACE = "replace"
    INSERT = "insert"
    DELETE = "delete"
    WRAP = "wrap"
    SPLIT = "split"
    MODERNIZE = "modernize"


@dataclass
class SyntaxIssue:
    """Information about a syntax issue detected in OpenSCAD code."""
    issue_type: SyntaxIssueType
    line_number: int
    column_start: int
    column_end: int
    original_text: str
    message: str
    severity: str  # "error", "warning", "info"
    min_version_required: Optional[str] = None
    suggested_replacement: Optional[str] = None
    migration_notes: Optional[str] = None


@dataclass
class MigrationRule:
    """Rule for migrating OpenSCAD syntax between versions."""
    rule_id: str
    name: str
    description: str
    from_version: str
    to_version: str
    pattern: str  # Regex pattern to match
    replacement: str  # Replacement pattern
    action: MigrationAction
    confidence: float  # 0.0 to 1.0
    validation_pattern: Optional[str] = None  # Pattern to validate result
    notes: Optional[str] = None


@dataclass
class MigrationSuggestion:
    """Suggestion for migrating a piece of code."""
    rule: MigrationRule
    issue: SyntaxIssue
    original_code: str
    suggested_code: str
    confidence: float
    explanation: str
    requires_manual_review: bool = False


@dataclass
class MigrationResult:
    """Result of applying migrations to OpenSCAD code."""
    success: bool
    original_code: str
    migrated_code: str
    applied_rules: List[MigrationRule]
    suggestions: List[MigrationSuggestion]
    issues_found: List[SyntaxIssue]
    issues_resolved: List[SyntaxIssue]
    manual_review_required: List[SyntaxIssue]
    migration_notes: List[str]
    performance_impact: Optional[str] = None


class OpenSCADSyntaxAnalyzer:
    """Analyzes OpenSCAD code for syntax issues and version compatibility."""
    
    def __init__(self):
        """Initialize the syntax analyzer."""
        self.known_functions = self._load_known_functions()
        self.version_features = self._load_version_features()
        self.deprecated_patterns = self._load_deprecated_patterns()
    
    def _load_known_functions(self) -> Dict[str, Dict]:
        """Load known OpenSCAD functions and their version requirements."""
        return {
            # Basic 3D primitives (available in all versions)
            "cube": {"min_version": "2015.03", "category": "primitive"},
            "sphere": {"min_version": "2015.03", "category": "primitive"},
            "cylinder": {"min_version": "2015.03", "category": "primitive"},
            "polyhedron": {"min_version": "2015.03", "category": "primitive"},
            
            # 2D primitives
            "square": {"min_version": "2015.03", "category": "primitive_2d"},
            "circle": {"min_version": "2015.03", "category": "primitive_2d"},
            "polygon": {"min_version": "2015.03", "category": "primitive_2d"},
            
            # Boolean operations
            "union": {"min_version": "2015.03", "category": "boolean"},
            "difference": {"min_version": "2015.03", "category": "boolean"},
            "intersection": {"min_version": "2015.03", "category": "boolean"},
            
            # Transformations
            "translate": {"min_version": "2015.03", "category": "transform"},
            "rotate": {"min_version": "2015.03", "category": "transform"},
            "scale": {"min_version": "2015.03", "category": "transform"},
            "resize": {"min_version": "2015.03", "category": "transform"},
            "mirror": {"min_version": "2015.03", "category": "transform"},
            "hull": {"min_version": "2015.03", "category": "transform"},
            "minkowski": {"min_version": "2015.03", "category": "transform"},
            
            # Text (newer feature)
            "text": {"min_version": "2019.05", "category": "primitive"},
            
            # Mathematical functions
            "sin": {"min_version": "2015.03", "category": "math"},
            "cos": {"min_version": "2015.03", "category": "math"},
            "tan": {"min_version": "2015.03", "category": "math"},
            "abs": {"min_version": "2015.03", "category": "math"},
            "pow": {"min_version": "2015.03", "category": "math"},
            "sqrt": {"min_version": "2015.03", "category": "math"},
            "exp": {"min_version": "2015.03", "category": "math"},
            "ln": {"min_version": "2015.03", "category": "math"},
            "log": {"min_version": "2015.03", "category": "math"},
            
            # List functions
            "len": {"min_version": "2015.03", "category": "list"},
            "concat": {"min_version": "2015.03", "category": "list"},
            
            # Newer functions and features
            "assert": {"min_version": "2019.05", "category": "debugging"},
            "echo": {"min_version": "2015.03", "category": "debugging"},
            
            # Import/include
            "include": {"min_version": "2015.03", "category": "file"},
            "use": {"min_version": "2015.03", "category": "file"},
            "import": {"min_version": "2015.03", "category": "file"},
        }
    
    def _load_version_features(self) -> Dict[str, List[str]]:
        """Load version-specific features and syntax."""
        return {
            "2015.03": [
                "basic_primitives", "boolean_operations", "transformations",
                "modules", "functions", "variables", "for_loops", "if_statements"
            ],
            "2019.05": [
                "text_primitive", "assert_function", "improved_list_comprehensions"
            ],
            "2021.01": [
                "improved_performance", "better_error_messages"
            ],
            "2022.03": [
                "list_comprehensions_enhanced", "function_literals"
            ],
            "2023.06": [
                "exponent_operator", "improved_text_handling", "better_unicode_support"
            ]
        }
    
    def _load_deprecated_patterns(self) -> List[Dict]:
        """Load patterns for deprecated syntax."""
        return [
            {
                "pattern": r"assign\s*\(",
                "message": "assign() is deprecated, use direct assignment",
                "replacement": "// Use direct assignment: variable = value;",
                "severity": "warning",
                "deprecated_in": "2019.05"
            },
            {
                "pattern": r"child\s*\(\s*\d+\s*\)",
                "message": "child() is deprecated, use children() instead",
                "replacement": "children()",
                "severity": "warning", 
                "deprecated_in": "2019.05"
            },
            {
                "pattern": r"import_stl\s*\(",
                "message": "import_stl() is deprecated, use import() instead",
                "replacement": "import()",
                "severity": "warning",
                "deprecated_in": "2019.05"
            },
            {
                "pattern": r"import_dxf\s*\(",
                "message": "import_dxf() is deprecated, use import() instead", 
                "replacement": "import()",
                "severity": "warning",
                "deprecated_in": "2019.05"
            }
        ]
    
    def analyze_scad_code(self, scad_code: str) -> List[SyntaxIssue]:
        """
        Analyze OpenSCAD code for syntax issues.
        
        Args:
            scad_code: OpenSCAD code to analyze
            
        Returns:
            List of detected syntax issues
        """
        issues = []
        lines = scad_code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check for deprecated patterns
            issues.extend(self._check_deprecated_patterns(line, line_num))
            
            # Check for version-specific features
            issues.extend(self._check_version_features(line, line_num))
            
            # Check for performance issues
            issues.extend(self._check_performance_issues(line, line_num))
            
            # Check for modernization opportunities
            issues.extend(self._check_modernization_opportunities(line, line_num))
        
        # Check for overall structure issues
        issues.extend(self._check_structure_issues(scad_code))
        
        return issues
    
    def _check_deprecated_patterns(self, line: str, line_num: int) -> List[SyntaxIssue]:
        """Check for deprecated syntax patterns."""
        issues = []
        
        for pattern_info in self.deprecated_patterns:
            pattern = pattern_info["pattern"]
            matches = re.finditer(pattern, line, re.IGNORECASE)
            
            for match in matches:
                issue = SyntaxIssue(
                    issue_type=SyntaxIssueType.DEPRECATED_SYNTAX,
                    line_number=line_num,
                    column_start=match.start(),
                    column_end=match.end(),
                    original_text=match.group(),
                    message=pattern_info["message"],
                    severity=pattern_info["severity"],
                    suggested_replacement=pattern_info["replacement"],
                    migration_notes=f"Deprecated in {pattern_info['deprecated_in']}"
                )
                issues.append(issue)
        
        return issues
    
    def _check_version_features(self, line: str, line_num: int) -> List[SyntaxIssue]:
        """Check for version-specific features."""
        issues = []
        
        # Check for exponent operator (2023.06+)
        if "**" in line:
            matches = re.finditer(r'\*\*', line)
            for match in matches:
                issue = SyntaxIssue(
                    issue_type=SyntaxIssueType.VERSION_INCOMPATIBLE,
                    line_number=line_num,
                    column_start=match.start(),
                    column_end=match.end(),
                    original_text="**",
                    message="Exponent operator requires OpenSCAD 2023.06 or later",
                    severity="error",
                    min_version_required="2023.06",
                    suggested_replacement="pow(base, exponent)",
                    migration_notes="Use pow() function for older versions"
                )
                issues.append(issue)
        
        # Check for assert function (2019.05+)
        if "assert(" in line:
            matches = re.finditer(r'assert\s*\(', line)
            for match in matches:
                issue = SyntaxIssue(
                    issue_type=SyntaxIssueType.VERSION_INCOMPATIBLE,
                    line_number=line_num,
                    column_start=match.start(),
                    column_end=match.end(),
                    original_text=match.group(),
                    message="assert() function requires OpenSCAD 2019.05 or later",
                    severity="warning",
                    min_version_required="2019.05",
                    migration_notes="Remove assert() calls for older versions"
                )
                issues.append(issue)
        
        # Check for text primitive (2019.05+)
        if "text(" in line:
            matches = re.finditer(r'text\s*\(', line)
            for match in matches:
                issue = SyntaxIssue(
                    issue_type=SyntaxIssueType.VERSION_INCOMPATIBLE,
                    line_number=line_num,
                    column_start=match.start(),
                    column_end=match.end(),
                    original_text=match.group(),
                    message="text() primitive requires OpenSCAD 2019.05 or later",
                    severity="warning",
                    min_version_required="2019.05",
                    migration_notes="Use external text generation for older versions"
                )
                issues.append(issue)
        
        return issues
    
    def _check_performance_issues(self, line: str, line_num: int) -> List[SyntaxIssue]:
        """Check for potential performance issues."""
        issues = []
        
        # Check for excessive union operations
        union_count = line.count("union(")
        if union_count > 10:
            issue = SyntaxIssue(
                issue_type=SyntaxIssueType.PERFORMANCE_WARNING,
                line_number=line_num,
                column_start=0,
                column_end=len(line),
                original_text=line.strip(),
                message=f"Line contains {union_count} union operations, consider optimization",
                severity="info",
                suggested_replacement="Consider grouping operations or using hull()",
                migration_notes="Large numbers of union operations can be slow"
            )
            issues.append(issue)
        
        # Check for nested for loops
        if "for" in line and line.count("for") > 1:
            issue = SyntaxIssue(
                issue_type=SyntaxIssueType.PERFORMANCE_WARNING,
                line_number=line_num,
                column_start=0,
                column_end=len(line),
                original_text=line.strip(),
                message="Nested for loops detected, may impact performance",
                severity="info",
                migration_notes="Consider alternative approaches for complex iterations"
            )
            issues.append(issue)
        
        return issues
    
    def _check_modernization_opportunities(self, line: str, line_num: int) -> List[SyntaxIssue]:
        """Check for modernization opportunities."""
        issues = []
        
        # Suggest list comprehensions where appropriate
        if re.search(r'for\s*\([^)]+\)\s*\{[^}]*\}', line):
            issue = SyntaxIssue(
                issue_type=SyntaxIssueType.MODERNIZATION_OPPORTUNITY,
                line_number=line_num,
                column_start=0,
                column_end=len(line),
                original_text=line.strip(),
                message="Consider using list comprehension for better readability",
                severity="info",
                suggested_replacement="[for (item = list) expression]",
                migration_notes="List comprehensions are more concise and readable"
            )
            issues.append(issue)
        
        # Suggest pow() instead of repeated multiplication
        if re.search(r'\w+\s*\*\s*\w+\s*\*\s*\w+', line):
            issue = SyntaxIssue(
                issue_type=SyntaxIssueType.MODERNIZATION_OPPORTUNITY,
                line_number=line_num,
                column_start=0,
                column_end=len(line),
                original_text=line.strip(),
                message="Consider using pow() function for exponentiation",
                severity="info",
                suggested_replacement="pow(base, exponent)",
                migration_notes="pow() is clearer for exponentiation operations"
            )
            issues.append(issue)
        
        return issues
    
    def _check_structure_issues(self, scad_code: str) -> List[SyntaxIssue]:
        """Check for overall structure issues."""
        issues = []
        
        # Check for very long lines
        lines = scad_code.split('\n')
        for line_num, line in enumerate(lines, 1):
            if len(line) > 120:
                issue = SyntaxIssue(
                    issue_type=SyntaxIssueType.MODERNIZATION_OPPORTUNITY,
                    line_number=line_num,
                    column_start=0,
                    column_end=len(line),
                    original_text=line[:50] + "..." if len(line) > 50 else line,
                    message=f"Long line ({len(line)} characters), consider breaking up",
                    severity="info",
                    migration_notes="Break long lines for better readability"
                )
                issues.append(issue)
        
        # Check for missing module documentation
        if "module " in scad_code and "/*" not in scad_code and "//" not in scad_code:
            issue = SyntaxIssue(
                issue_type=SyntaxIssueType.MODERNIZATION_OPPORTUNITY,
                line_number=1,
                column_start=0,
                column_end=0,
                original_text="",
                message="Consider adding documentation comments to modules",
                severity="info",
                migration_notes="Documentation improves code maintainability"
            )
            issues.append(issue)
        
        return issues
    
    def get_minimum_version_required(self, scad_code: str) -> str:
        """
        Determine the minimum OpenSCAD version required for the code.
        
        Args:
            scad_code: OpenSCAD code to analyze
            
        Returns:
            Minimum version string required
        """
        issues = self.analyze_scad_code(scad_code)
        
        # Find the highest minimum version requirement
        min_versions = []
        for issue in issues:
            if issue.min_version_required:
                min_versions.append(issue.min_version_required)
        
        if not min_versions:
            return "2015.03"  # Default minimum supported version
        
        # Sort versions and return the latest
        version_list = []
        for version_str in min_versions:
            try:
                parts = version_str.split(".")
                major = int(parts[0])
                minor = int(parts[1]) if len(parts) > 1 else 0
                version_list.append((major, minor, version_str))
            except (ValueError, IndexError):
                continue
        
        if version_list:
            version_list.sort(reverse=True)
            return version_list[0][2]
        
        return "2015.03"


class MigrationEngine:
    """Engine for migrating OpenSCAD code between versions."""
    
    def __init__(self):
        """Initialize the migration engine."""
        self.migration_rules = self._load_migration_rules()
        self.syntax_analyzer = OpenSCADSyntaxAnalyzer()
    
    def _load_migration_rules(self) -> List[MigrationRule]:
        """Load migration rules for different version transitions."""
        return [
            # Deprecation fixes
            MigrationRule(
                rule_id="fix_assign_deprecated",
                name="Fix deprecated assign()",
                description="Replace deprecated assign() with direct assignment",
                from_version="any",
                to_version="2019.05+",
                pattern=r'assign\s*\(\s*([^=]+)\s*=\s*([^)]+)\s*\)',
                replacement=r'\1 = \2;',
                action=MigrationAction.REPLACE,
                confidence=0.9,
                notes="assign() was deprecated in favor of direct assignment"
            ),
            
            MigrationRule(
                rule_id="fix_child_deprecated",
                name="Fix deprecated child()",
                description="Replace child() with children()",
                from_version="any",
                to_version="2019.05+",
                pattern=r'child\s*\(\s*(\d+)\s*\)',
                replacement=r'children(\1)',
                action=MigrationAction.REPLACE,
                confidence=0.95,
                notes="child() was replaced with children()"
            ),
            
            # Import function modernization
            MigrationRule(
                rule_id="modernize_import_stl",
                name="Modernize import_stl()",
                description="Replace import_stl() with import()",
                from_version="any",
                to_version="2019.05+",
                pattern=r'import_stl\s*\(',
                replacement='import(',
                action=MigrationAction.REPLACE,
                confidence=0.95,
                notes="import_stl() was replaced with generic import()"
            ),
            
            MigrationRule(
                rule_id="modernize_import_dxf",
                name="Modernize import_dxf()",
                description="Replace import_dxf() with import()",
                from_version="any", 
                to_version="2019.05+",
                pattern=r'import_dxf\s*\(',
                replacement='import(',
                action=MigrationAction.REPLACE,
                confidence=0.95,
                notes="import_dxf() was replaced with generic import()"
            ),
            
            # Version compatibility fixes
            MigrationRule(
                rule_id="fix_exponent_operator",
                name="Fix exponent operator compatibility",
                description="Replace ** operator with pow() for older versions",
                from_version="2023.06",
                to_version="pre-2023.06",
                pattern=r'(\w+|\([^)]+\))\s*\*\*\s*(\w+|\([^)]+\))',
                replacement=r'pow(\1, \2)',
                action=MigrationAction.REPLACE,
                confidence=0.9,
                notes="** operator requires OpenSCAD 2023.06+"
            ),
            
            # Performance optimizations
            MigrationRule(
                rule_id="optimize_repeated_union",
                name="Optimize repeated union operations",
                description="Group multiple union operations for better performance",
                from_version="any",
                to_version="any",
                pattern=r'union\s*\(\s*\)\s*\{\s*(.+?)\s*union\s*\(\s*\)\s*\{\s*(.+?)\s*\}',
                replacement=r'union() {\1 \2 }',
                action=MigrationAction.REPLACE,
                confidence=0.7,
                notes="Grouping union operations can improve performance"
            ),
            
            # Modernization suggestions
            MigrationRule(
                rule_id="suggest_list_comprehension",
                name="Suggest list comprehension",
                description="Convert for loops to list comprehensions where appropriate",
                from_version="any",
                to_version="2022.03+",
                pattern=r'for\s*\(\s*(\w+)\s*=\s*(.+?)\s*\)\s*(.+)',
                replacement=r'[for (\1 = \2) \3]',
                action=MigrationAction.MODERNIZE,
                confidence=0.6,
                notes="List comprehensions are more concise and readable"
            )
        ]
    
    def create_migration_plan(self, scad_code: str, from_version: str, 
                            to_version: str) -> List[MigrationSuggestion]:
        """
        Create a migration plan for upgrading code between versions.
        
        Args:
            scad_code: OpenSCAD code to migrate
            from_version: Current version compatibility
            to_version: Target version compatibility
            
        Returns:
            List of migration suggestions
        """
        suggestions = []
        
        # Analyze current code for issues
        issues = self.syntax_analyzer.analyze_scad_code(scad_code)
        
        # Find applicable migration rules
        applicable_rules = self._find_applicable_rules(from_version, to_version)
        
        # Generate suggestions for each applicable rule
        for rule in applicable_rules:
            matches = re.finditer(rule.pattern, scad_code, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                # Apply the rule to generate suggestion
                try:
                    suggested_code = re.sub(rule.pattern, rule.replacement, match.group())
                    
                    # Find corresponding issue if any
                    corresponding_issue = None
                    for issue in issues:
                        if (issue.line_number == self._get_line_number(scad_code, match.start()) and
                            issue.original_text in match.group()):
                            corresponding_issue = issue
                            break
                    
                    # Create suggestion
                    suggestion = MigrationSuggestion(
                        rule=rule,
                        issue=corresponding_issue,
                        original_code=match.group(),
                        suggested_code=suggested_code,
                        confidence=rule.confidence,
                        explanation=rule.description,
                        requires_manual_review=(rule.confidence < 0.8)
                    )
                    suggestions.append(suggestion)
                    
                except Exception as e:
                    logger.warning(f"Failed to apply rule {rule.rule_id}: {e}")
                    continue
        
        return suggestions
    
    def apply_migration(self, scad_code: str, suggestions: List[MigrationSuggestion],
                       auto_apply_threshold: float = 0.8) -> MigrationResult:
        """
        Apply migration suggestions to OpenSCAD code.
        
        Args:
            scad_code: Original OpenSCAD code
            suggestions: List of migration suggestions to apply
            auto_apply_threshold: Confidence threshold for auto-applying changes
            
        Returns:
            Migration result with applied changes
        """
        migrated_code = scad_code
        applied_rules = []
        manual_review_items = []
        migration_notes = []
        
        # Sort suggestions by confidence (highest first)
        sorted_suggestions = sorted(suggestions, key=lambda s: s.confidence, reverse=True)
        
        for suggestion in sorted_suggestions:
            if suggestion.confidence >= auto_apply_threshold:
                # Auto-apply high-confidence suggestions
                try:
                    migrated_code = re.sub(
                        suggestion.rule.pattern,
                        suggestion.rule.replacement,
                        migrated_code,
                        count=1  # Apply one at a time for better control
                    )
                    applied_rules.append(suggestion.rule)
                    migration_notes.append(f"Applied: {suggestion.rule.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to apply suggestion {suggestion.rule.rule_id}: {e}")
                    manual_review_items.append(suggestion.issue)
            else:
                # Flag low-confidence suggestions for manual review
                if suggestion.issue:
                    manual_review_items.append(suggestion.issue)
                migration_notes.append(f"Manual review needed: {suggestion.rule.name}")
        
        # Analyze final code for remaining issues
        final_issues = self.syntax_analyzer.analyze_scad_code(migrated_code)
        original_issues = self.syntax_analyzer.analyze_scad_code(scad_code)
        
        # Determine resolved issues
        resolved_issues = []
        for original_issue in original_issues:
            is_resolved = True
            for final_issue in final_issues:
                if (original_issue.original_text == final_issue.original_text and
                    original_issue.line_number == final_issue.line_number):
                    is_resolved = False
                    break
            if is_resolved:
                resolved_issues.append(original_issue)
        
        return MigrationResult(
            success=len(applied_rules) > 0 or len(manual_review_items) == 0,
            original_code=scad_code,
            migrated_code=migrated_code,
            applied_rules=applied_rules,
            suggestions=suggestions,
            issues_found=original_issues,
            issues_resolved=resolved_issues,
            manual_review_required=manual_review_items,
            migration_notes=migration_notes,
            performance_impact="Migration may improve performance" if any(
                "performance" in rule.description.lower() for rule in applied_rules
            ) else None
        )
    
    def validate_migrated_code(self, original_code: str, migrated_code: str) -> Dict[str, any]:
        """
        Validate that migrated code maintains functional equivalence.
        
        Args:
            original_code: Original OpenSCAD code
            migrated_code: Migrated OpenSCAD code
            
        Returns:
            Validation result with analysis
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "structural_changes": [],
            "syntax_improvements": []
        }
        
        # Basic structural analysis
        original_lines = len(original_code.split('\n'))
        migrated_lines = len(migrated_code.split('\n'))
        
        if abs(original_lines - migrated_lines) > original_lines * 0.2:
            validation_result["warnings"].append(
                f"Significant line count change: {original_lines} → {migrated_lines}"
            )
        
        # Check for preserved module/function definitions
        original_modules = re.findall(r'module\s+(\w+)', original_code)
        migrated_modules = re.findall(r'module\s+(\w+)', migrated_code)
        
        if set(original_modules) != set(migrated_modules):
            validation_result["errors"].append(
                "Module definitions changed during migration"
            )
            validation_result["is_valid"] = False
        
        # Check for preserved function definitions
        original_functions = re.findall(r'function\s+(\w+)', original_code)
        migrated_functions = re.findall(r'function\s+(\w+)', migrated_code)
        
        if set(original_functions) != set(migrated_functions):
            validation_result["errors"].append(
                "Function definitions changed during migration"
            )
            validation_result["is_valid"] = False
        
        # Analyze syntax improvements
        original_issues = self.syntax_analyzer.analyze_scad_code(original_code)
        migrated_issues = self.syntax_analyzer.analyze_scad_code(migrated_code)
        
        if len(migrated_issues) < len(original_issues):
            validation_result["syntax_improvements"].append(
                f"Resolved {len(original_issues) - len(migrated_issues)} syntax issues"
            )
        
        return validation_result
    
    def _find_applicable_rules(self, from_version: str, to_version: str) -> List[MigrationRule]:
        """Find migration rules applicable for the version transition."""
        applicable_rules = []
        
        for rule in self.migration_rules:
            # Check if rule applies to this version transition
            if (rule.from_version == "any" or 
                self._version_matches(from_version, rule.from_version)):
                if (rule.to_version == "any" or 
                    self._version_matches(to_version, rule.to_version)):
                    applicable_rules.append(rule)
        
        return applicable_rules
    
    def _version_matches(self, version: str, pattern: str) -> bool:
        """Check if version matches pattern."""
        if pattern == "any":
            return True
        
        if pattern.endswith("+"):
            # Handle "2019.05+" pattern
            base_version = pattern[:-1]
            return self._compare_versions(version, base_version) >= 0
        
        if pattern.startswith("pre-"):
            # Handle "pre-2023.06" pattern
            base_version = pattern[4:]
            return self._compare_versions(version, base_version) < 0
        
        return version == pattern
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings. Returns -1, 0, or 1."""
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
    
    def _get_line_number(self, text: str, position: int) -> int:
        """Get line number for a character position in text."""
        return text[:position].count('\n') + 1
    
    def generate_migration_report(self, result: MigrationResult) -> str:
        """
        Generate a human-readable migration report.
        
        Args:
            result: Migration result to report on
            
        Returns:
            Formatted migration report
        """
        report_lines = []
        
        report_lines.append("# OpenSCAD Migration Report")
        report_lines.append("=" * 40)
        report_lines.append(f"Migration Status: {'✅ Success' if result.success else '❌ Failed'}")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary statistics
        report_lines.append("## Summary")
        report_lines.append(f"- Applied Rules: {len(result.applied_rules)}")
        report_lines.append(f"- Issues Found: {len(result.issues_found)}")
        report_lines.append(f"- Issues Resolved: {len(result.issues_resolved)}")
        report_lines.append(f"- Manual Review Required: {len(result.manual_review_required)}")
        report_lines.append("")
        
        # Applied rules
        if result.applied_rules:
            report_lines.append("## Applied Migration Rules")
            for rule in result.applied_rules:
                report_lines.append(f"### {rule.name}")
                report_lines.append(f"- Description: {rule.description}")
                report_lines.append(f"- Confidence: {rule.confidence:.1%}")
                if rule.notes:
                    report_lines.append(f"- Notes: {rule.notes}")
                report_lines.append("")
        
        # Manual review items
        if result.manual_review_required:
            report_lines.append("## Manual Review Required")
            for issue in result.manual_review_required:
                report_lines.append(f"### Line {issue.line_number}: {issue.message}")
                report_lines.append(f"- Original: `{issue.original_text}`")
                if issue.suggested_replacement:
                    report_lines.append(f"- Suggested: `{issue.suggested_replacement}`")
                if issue.migration_notes:
                    report_lines.append(f"- Notes: {issue.migration_notes}")
                report_lines.append("")
        
        # Migration notes
        if result.migration_notes:
            report_lines.append("## Migration Notes")
            for note in result.migration_notes:
                report_lines.append(f"- {note}")
            report_lines.append("")
        
        # Performance impact
        if result.performance_impact:
            report_lines.append("## Performance Impact")
            report_lines.append(result.performance_impact)
            report_lines.append("")
        
        # Code changes
        if result.migrated_code != result.original_code:
            report_lines.append("## Code Changes")
            report_lines.append("### Original Code")
            report_lines.append("```openscad")
            report_lines.append(result.original_code)
            report_lines.append("```")
            report_lines.append("")
            report_lines.append("### Migrated Code")
            report_lines.append("```openscad")
            report_lines.append(result.migrated_code)
            report_lines.append("```")
        
        return "\n".join(report_lines)


# Convenience functions for easy access
def analyze_openscad_syntax(scad_code: str) -> List[SyntaxIssue]:
    """Quick syntax analysis of OpenSCAD code."""
    analyzer = OpenSCADSyntaxAnalyzer()
    return analyzer.analyze_scad_code(scad_code)


def migrate_openscad_code(scad_code: str, from_version: str, 
                         to_version: str) -> MigrationResult:
    """Quick migration of OpenSCAD code between versions."""
    engine = MigrationEngine()
    suggestions = engine.create_migration_plan(scad_code, from_version, to_version)
    return engine.apply_migration(scad_code, suggestions)


def get_minimum_openscad_version(scad_code: str) -> str:
    """Get minimum OpenSCAD version required for code."""
    analyzer = OpenSCADSyntaxAnalyzer()
    return analyzer.get_minimum_version_required(scad_code)