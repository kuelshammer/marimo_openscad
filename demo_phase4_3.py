#!/usr/bin/env python3
"""
Phase 4.3 Demo: Migration & Upgrade Tools + Community Model Testing

Demonstrates the new migration engine and community model testing capabilities:
- OpenSCAD syntax analysis and issue detection
- Automatic migration between OpenSCAD versions
- Community model compatibility testing
- Migration reports and recommendations
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for demo
sys.path.insert(0, str(Path(__file__).parent / "src"))

from marimo_openscad.migration_engine import (
    OpenSCADSyntaxAnalyzer,
    MigrationEngine,
    analyze_openscad_syntax,
    migrate_openscad_code,
    get_minimum_openscad_version
)

from marimo_openscad.community_model_tester import (
    CommunityModelRegistry,
    ModelDownloader,
    CommunityModelTester,
    test_popular_models
)


def demo_syntax_analyzer():
    """Demo OpenSCAD syntax analysis functionality."""
    
    print("🔍 Phase 4.3 Demo: Migration & Upgrade Tools")
    print("=" * 50)
    
    print("\n📋 OpenSCAD Syntax Analyzer:")
    print("-" * 30)
    
    # Create analyzer
    analyzer = OpenSCADSyntaxAnalyzer()
    
    print(f"Known functions: {len(analyzer.known_functions)}")
    print(f"Version features: {len(analyzer.version_features)}")
    print(f"Deprecated patterns: {len(analyzer.deprecated_patterns)}")
    
    # Test various OpenSCAD code samples
    test_cases = [
        {
            "name": "Basic OpenSCAD",
            "code": "cube([10, 10, 10]);"
        },
        {
            "name": "Deprecated assign()",
            "code": "assign(x = 10) cube([x, x, x]);"
        },
        {
            "name": "Exponent operator (2023.06+)",
            "code": "cube([10**2, 10, 10]);"
        },
        {
            "name": "Multiple issues",
            "code": '''
            assign(size = 5)
            assign(height = 10)
            
            module gear() {
                import_stl("gear.stl");
                child(0);
            }
            
            cube([size**2, height, 10]);
            '''
        },
        {
            "name": "Modern features",
            "code": '''
            assert(true, "Test assertion");
            text("Hello World", size=12);
            cube([10, 10, 10]);
            '''
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 Analyzing: {test_case['name']}")
        print(f"Code: {test_case['code'][:50]}{'...' if len(test_case['code']) > 50 else ''}")
        
        issues = analyzer.analyze_scad_code(test_case['code'])
        min_version = analyzer.get_minimum_version_required(test_case['code'])
        
        print(f"   Issues found: {len(issues)}")
        print(f"   Minimum version: {min_version}")
        
        if issues:
            for issue in issues[:3]:  # Show first 3 issues
                print(f"   • Line {issue.line_number}: {issue.message} ({issue.severity})")
                if issue.min_version_required:
                    print(f"     Requires: {issue.min_version_required}")


def demo_migration_engine():
    """Demo migration engine functionality."""
    
    print("\n🔄 Migration Engine:")
    print("-" * 20)
    
    # Create migration engine
    engine = MigrationEngine()
    
    print(f"Migration rules: {len(engine.migration_rules)}")
    
    # Show some available rules
    print("\n📋 Available Migration Rules:")
    for rule in engine.migration_rules[:5]:  # Show first 5
        print(f"  • {rule.name}")
        print(f"    From: {rule.from_version} → To: {rule.to_version}")
        print(f"    Confidence: {rule.confidence:.1%}")
    
    # Test migration scenarios
    migration_scenarios = [
        {
            "name": "Fix deprecated assign()",
            "code": "assign(x = 10) assign(y = 5) cube([x, y, 10]);",
            "from_version": "2015.03",
            "to_version": "2019.05+"
        },
        {
            "name": "Fix deprecated child()",
            "code": "module test() { child(0); child(1); }",
            "from_version": "2015.03", 
            "to_version": "2019.05+"
        },
        {
            "name": "Fix import functions",
            "code": 'import_stl("model.stl"); import_dxf("drawing.dxf");',
            "from_version": "2015.03",
            "to_version": "2019.05+"
        },
        {
            "name": "Compatibility: exponent operator",
            "code": "cube([x**2, y**3, 10]);",
            "from_version": "2023.06",
            "to_version": "pre-2023.06"
        }
    ]
    
    print(f"\n🔧 Migration Scenarios:")
    for scenario in migration_scenarios:
        print(f"\n📝 {scenario['name']}:")
        print(f"   Original: {scenario['code'][:60]}{'...' if len(scenario['code']) > 60 else ''}")
        print(f"   Migration: {scenario['from_version']} → {scenario['to_version']}")
        
        # Create migration plan
        suggestions = engine.create_migration_plan(
            scenario['code'], 
            scenario['from_version'], 
            scenario['to_version']
        )
        
        print(f"   Suggestions: {len(suggestions)}")
        
        if suggestions:
            # Apply migration
            result = engine.apply_migration(scenario['code'], suggestions)
            
            print(f"   Success: {result.success}")
            print(f"   Applied rules: {len(result.applied_rules)}")
            
            if result.migrated_code != scenario['code']:
                print(f"   Migrated: {result.migrated_code[:60]}{'...' if len(result.migrated_code) > 60 else ''}")
            
            if result.manual_review_required:
                print(f"   Manual review: {len(result.manual_review_required)} items")


def demo_migration_workflow():
    """Demo complete migration workflow."""
    
    print("\n🛠️ Complete Migration Workflow:")
    print("-" * 35)
    
    # Legacy OpenSCAD code with multiple issues
    legacy_code = '''
    // Legacy OpenSCAD model (pre-2019)
    assign(gear_radius = 15)
    assign(gear_height = 8)
    assign(tooth_count = 12)
    
    module gear_tooth() {
        import_stl("tooth_profile.stl");
    }
    
    module gear() {
        cylinder(r=gear_radius, h=gear_height);
        
        for (i = [0:tooth_count-1]) {
            rotate([0, 0, i * (360/tooth_count)])
            translate([gear_radius + 2, 0, 0])
            child(0);
        }
    }
    
    gear() gear_tooth();
    '''
    
    print("📝 Legacy Code Analysis:")
    print(f"   Lines of code: {len(legacy_code.split())}")
    
    # Step 1: Analyze issues
    print("\n1️⃣ Syntax Analysis:")
    issues = analyze_openscad_syntax(legacy_code)
    print(f"   Issues found: {len(issues)}")
    
    for issue in issues:
        print(f"   • Line {issue.line_number}: {issue.message}")
        if issue.suggested_replacement:
            print(f"     Suggested: {issue.suggested_replacement}")
    
    # Step 2: Determine minimum version
    min_version = get_minimum_openscad_version(legacy_code)
    print(f"\n2️⃣ Version Requirements:")
    print(f"   Minimum version: {min_version}")
    
    # Step 3: Migration to modern OpenSCAD
    print(f"\n3️⃣ Migration Process:")
    migration_result = migrate_openscad_code(legacy_code, "2015.03", "2019.05+")
    
    print(f"   Migration success: {migration_result.success}")
    print(f"   Applied rules: {len(migration_result.applied_rules)}")
    print(f"   Issues resolved: {len(migration_result.issues_resolved)}")
    print(f"   Manual review needed: {len(migration_result.manual_review_required)}")
    
    # Step 4: Show migration results
    print(f"\n4️⃣ Migration Results:")
    if migration_result.migrated_code != legacy_code:
        print("   ✅ Code was successfully migrated")
        print(f"   Original length: {len(legacy_code)} chars")
        print(f"   Migrated length: {len(migration_result.migrated_code)} chars")
        
        # Show first few lines of migrated code
        migrated_lines = migration_result.migrated_code.split('\n')[:5]
        print("   Preview of migrated code:")
        for i, line in enumerate(migrated_lines, 1):
            if line.strip():
                print(f"     {i}: {line.strip()}")
    else:
        print("   ⚠️ No migration changes were applied")
    
    # Step 5: Validation
    print(f"\n5️⃣ Validation:")
    engine = MigrationEngine()
    validation = engine.validate_migrated_code(legacy_code, migration_result.migrated_code)
    
    print(f"   Validation passed: {validation['is_valid']}")
    if validation['warnings']:
        print(f"   Warnings: {len(validation['warnings'])}")
    if validation['errors']:
        print(f"   Errors: {len(validation['errors'])}")
    
    # Step 6: Generate report
    print(f"\n6️⃣ Migration Report:")
    engine = MigrationEngine()
    report = engine.generate_migration_report(migration_result)
    
    print("   📊 Report generated successfully")
    print(f"   Report size: {len(report)} characters")
    print("   Report sections: Summary, Applied Rules, Manual Review, Code Changes")


def demo_community_model_registry():
    """Demo community model registry functionality."""
    
    print("\n📚 Community Model Registry:")
    print("-" * 30)
    
    # Create registry
    registry = CommunityModelRegistry()
    
    print(f"Total models: {len(registry.models)}")
    
    # Show popular models
    popular = registry.get_popular_models(5)
    print(f"\n🌟 Top {len(popular)} Popular Models:")
    
    for i, model in enumerate(popular, 1):
        print(f"  {i}. {model.name}")
        print(f"     Author: {model.author}")
        print(f"     Tags: {', '.join(model.tags)}")
        print(f"     Popularity: {model.popularity_score}/100")
        print(f"     Size: {model.file_size} bytes")
    
    # Show models by category
    print(f"\n🔧 Mechanical Models:")
    mechanical = registry.get_models_by_tag("mechanical")
    for model in mechanical[:3]:
        print(f"  • {model.name} by {model.author}")
    
    print(f"\n🎨 Decorative Models:")
    decorative = registry.get_models_by_tag("decorative")
    for model in decorative[:3]:
        print(f"  • {model.name} by {model.author}")
    
    # Test model lookup
    print(f"\n🔍 Model Lookup Test:")
    if registry.models:
        test_model = registry.get_model_by_name(registry.models[0].name)
        if test_model:
            print(f"  ✅ Found: {test_model.name}")
        else:
            print(f"  ❌ Not found")


async def demo_model_downloader():
    """Demo model downloader functionality."""
    
    print("\n📥 Model Downloader:")
    print("-" * 20)
    
    # Create downloader with temporary directory
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    downloader = ModelDownloader(cache_dir=temp_dir)
    
    print(f"Cache directory: {downloader.cache_dir}")
    print(f"Timeout: {downloader.timeout_seconds}s")
    
    # Test content validation
    print(f"\n🔍 Content Validation Tests:")
    
    valid_content = '''
    module test_gear() {
        cylinder(r=5, h=10);
        for (i = [0:8]) {
            rotate([0, 0, i * 40])
            translate([7, 0, 0])
            cube([1, 1, 10]);
        }
    }
    '''
    
    invalid_content = '''
    This is just plain text.
    No OpenSCAD constructs here.
    '''
    
    print(f"  Valid OpenSCAD content: {downloader._validate_scad_content(valid_content)}")
    print(f"  Invalid content: {downloader._validate_scad_content(invalid_content)}")
    
    # Test cache management
    print(f"\n🗂️ Cache Management:")
    
    # Create some test files to simulate cache
    for i in range(3):
        test_file = temp_dir / f"test_model_{i}.scad"
        test_file.write_text(f"// Test model {i}\ncube([{i+1}, {i+1}, {i+1}]);")
    
    print(f"  Created test files: {len(list(temp_dir.glob('*.scad')))}")
    
    # Clear cache
    cleared = downloader.clear_cache()
    print(f"  Cleared files: {cleared}")
    print(f"  Remaining files: {len(list(temp_dir.glob('*.scad')))}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


async def demo_community_model_tester():
    """Demo community model testing functionality."""
    
    print("\n🧪 Community Model Tester:")
    print("-" * 25)
    
    # Create tester
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    tester = CommunityModelTester(cache_dir=temp_dir)
    
    print(f"Target versions: {', '.join(tester.target_versions)}")
    print(f"Compatibility threshold: {tester.compatibility_threshold}")
    
    # Test individual model (mock)
    print(f"\n📝 Individual Model Test:")
    
    # Create mock model with test content
    test_content = '''
    // Test community model
    module parametric_gear(teeth=12, module=2) {
        gear_radius = teeth * module / 2;
        
        cylinder(r=gear_radius, h=5);
        
        for (i = [0:teeth-1]) {
            angle = i * (360/teeth);
            rotate([0, 0, angle])
            translate([gear_radius + 1, 0, 0])
            cube([1, 1, 5]);
        }
    }
    
    parametric_gear(teeth=16, module=1.5);
    '''
    
    model_file = temp_dir / "test_gear.scad"
    model_file.write_text(test_content)
    
    from marimo_openscad.community_model_tester import CommunityModel
    
    test_model = CommunityModel(
        name="Test Parametric Gear",
        source_url="https://example.com/gear",
        description="Test parametric gear generator",
        author="demo_author",
        license="MIT",
        tags=["gear", "parametric", "mechanical"],
        file_size=len(test_content),
        download_url="https://example.com/gear.scad",
        local_path=model_file
    )
    
    result = await tester.test_model(test_model)
    
    print(f"  Model: {result.model.name}")
    print(f"  Status: {result.test_status}")
    print(f"  Compatibility score: {result.compatibility_score:.2f}")
    print(f"  Minimum version: {result.minimum_version_required}")
    print(f"  Issues found: {len(result.syntax_issues)}")
    
    if result.notes:
        print(f"  Notes: {'; '.join(result.notes)}")
    
    # Test compatibility score calculation
    print(f"\n📊 Compatibility Scoring:")
    
    # Test with different scenarios
    from marimo_openscad.migration_engine import SyntaxIssue, SyntaxIssueType
    
    scenarios = [
        ([], "2019.05", "2023.06", "No issues"),
        ([SyntaxIssue(SyntaxIssueType.DEPRECATED_SYNTAX, 1, 0, 10, "test", "Warning", "warning")], 
         "2019.05", "2023.06", "Warning issue"),
        ([], "2023.06", "2019.05", "Version incompatibility")
    ]
    
    for issues, min_ver, target_ver, description in scenarios:
        score = tester._calculate_compatibility_score(issues, min_ver, target_ver)
        print(f"  {description}: {score:.2f}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


async def demo_integration_workflow():
    """Demo complete integration workflow."""
    
    print("\n🔗 Integration Workflow:")
    print("-" * 25)
    
    print("This workflow demonstrates how Phase 4.3 components work together:")
    print("1. Analyze community models for compatibility issues")
    print("2. Generate migration suggestions")
    print("3. Apply migrations where possible")
    print("4. Generate comprehensive reports")
    
    # Create sample problematic model
    problematic_model = '''
    // Community model with compatibility issues
    assign(gear_teeth = 24)
    assign(gear_module = 2)
    assign(gear_height = 5)
    
    module gear_profile() {
        import_stl("involute_profile.stl");
    }
    
    module gear() {
        base_radius = gear_teeth * gear_module / 2;
        
        // Base cylinder
        cylinder(r=base_radius, h=gear_height);
        
        // Gear teeth
        for (tooth = [0:gear_teeth-1]) {
            rotate([0, 0, tooth * (360/gear_teeth)])
            translate([base_radius + 1, 0, 0]) {
                child(0);
            }
        }
    }
    
    // Generate gear with profile
    gear() gear_profile();
    
    // Advanced calculation using newer syntax
    echo("Gear volume:", base_radius**2 * PI * gear_height);
    '''
    
    print(f"\n📋 Sample Model Analysis:")
    print(f"  Lines of code: {len(problematic_model.split())}")
    
    # Step 1: Syntax analysis
    issues = analyze_openscad_syntax(problematic_model)
    print(f"  Issues detected: {len(issues)}")
    
    # Categorize issues
    deprecated_issues = [i for i in issues if i.issue_type.value == "deprecated_syntax"]
    version_issues = [i for i in issues if i.issue_type.value == "version_incompatible"]
    
    print(f"  Deprecated syntax: {len(deprecated_issues)}")
    print(f"  Version incompatible: {len(version_issues)}")
    
    # Step 2: Migration analysis
    min_version = get_minimum_openscad_version(problematic_model)
    print(f"  Minimum version required: {min_version}")
    
    # Step 3: Migration suggestions
    migration_result = migrate_openscad_code(problematic_model, "2015.03", "2019.05+")
    
    print(f"\n🔧 Migration Results:")
    print(f"  Success: {migration_result.success}")
    print(f"  Rules applied: {len(migration_result.applied_rules)}")
    print(f"  Issues resolved: {len(migration_result.issues_resolved)}")
    
    # Step 4: Community compatibility assessment
    print(f"\n🌍 Community Compatibility:")
    print(f"  Pre-migration compatibility: Requires OpenSCAD {min_version}")
    
    if migration_result.success:
        new_min_version = get_minimum_openscad_version(migration_result.migrated_code)
        print(f"  Post-migration compatibility: Requires OpenSCAD {new_min_version}")
        
        if new_min_version != min_version:
            print(f"  ✅ Migration improved compatibility!")
        else:
            print(f"  ⚠️ Some issues remain for manual review")


async def main():
    """Main demo function."""
    
    print("🎉 Phase 4.3: Migration & Upgrade Tools + Community Testing Demo")
    print("=" * 70)
    print("Demonstrates syntax analysis, migration engine, and community")
    print("model testing for comprehensive OpenSCAD version compatibility.")
    
    try:
        # Demo all components
        demo_syntax_analyzer()
        demo_migration_engine()
        demo_migration_workflow()
        demo_community_model_registry()
        await demo_model_downloader()
        await demo_community_model_tester()
        await demo_integration_workflow()
        
        print("\n🎉 Phase 4.3 Demo Complete!")
        print("\nMigration & Upgrade Tools Features:")
        print("  ✅ OpenSCAD syntax analysis with issue detection")
        print("  ✅ Automatic migration rules for version compatibility")
        print("  ✅ Migration engine with confidence scoring")
        print("  ✅ Validation and migration reports")
        print("  ✅ Community model registry (10 popular models)")
        print("  ✅ Model download and caching system")
        print("  ✅ Comprehensive compatibility testing")
        print("  ✅ Integration workflow for end-to-end migration")
        
        print(f"\n📊 Summary:")
        print(f"   Migration rules: 7+ rules for common patterns")
        print(f"   Community models: 10 popular models tracked")
        print(f"   Target versions: 5 OpenSCAD versions supported")
        print(f"   Platform: {sys.platform}")
        print(f"   Python: {sys.version.split()[0]}")
        print(f"   Status: Phase 4.3 migration infrastructure complete")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())