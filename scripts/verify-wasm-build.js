#!/usr/bin/env node
/**
 * Verify WASM Build Integrity
 * 
 * This script verifies that the WASM build process completed successfully
 * and all required assets are present and valid.
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
}

async function checkFileExists(filePath, description) {
  try {
    const stats = await fs.stat(filePath);
    return {
      exists: true,
      size: stats.size,
      sizeFormatted: formatFileSize(stats.size),
      description
    };
  } catch {
    return {
      exists: false,
      description
    };
  }
}

async function validateJavaScriptModules(distDir) {
  console.log('🔍 Validating JavaScript modules...');
  
  const expectedModules = [
    { file: 'widget.es.js', description: 'Main widget module (ES)' },
    { file: 'widget.umd.js', description: 'Main widget module (UMD)' },
    { file: 'wasm-loader.es.js', description: 'WASM loader module (ES)' },
    { file: 'wasm-loader.umd.js', description: 'WASM loader module (UMD)' },
    { file: 'wasm-renderer.es.js', description: 'WASM renderer module (ES)' },
    { file: 'worker-manager.es.js', description: 'Worker manager module (ES)' },
    { file: 'memory-manager.es.js', description: 'Memory manager module (ES)' },
    { file: 'cache-manager.es.js', description: 'Cache manager module (ES)' },
    { file: 'openscad-worker.es.js', description: 'OpenSCAD worker module (ES)' }
  ];
  
  const validationResults = [];
  let validModules = 0;
  
  for (const module of expectedModules) {
    const filePath = path.join(distDir, module.file);
    const result = await checkFileExists(filePath, module.description);
    
    validationResults.push({
      ...module,
      ...result
    });
    
    if (result.exists) {
      console.log(`   ✅ ${module.file}: ${result.sizeFormatted}`);
      validModules++;
    } else {
      console.log(`   ❌ ${module.file}: Missing`);
    }
  }
  
  console.log(`   📊 Valid modules: ${validModules}/${expectedModules.length}`);
  
  return {
    total: expectedModules.length,
    valid: validModules,
    results: validationResults
  };
}

async function validateWasmAssets(distDir) {
  console.log('\n🔍 Validating WASM assets...');
  
  const wasmDir = path.join(distDir, 'wasm');
  
  // Check if wasm directory exists
  try {
    await fs.access(wasmDir);
  } catch {
    console.log('   ❌ WASM directory not found in dist/');
    return { total: 0, valid: 0, results: [] };
  }
  
  const expectedWasmFiles = [
    { file: 'openscad.wasm', description: 'OpenSCAD WASM binary', critical: true },
    { file: 'openscad.js', description: 'OpenSCAD JavaScript glue code', critical: true },
    { file: 'openscad.wasm.js', description: 'WASM loader JavaScript', critical: true },
    { file: 'openscad.d.ts', description: 'TypeScript definitions', critical: false },
    { file: 'openscad.fonts.js', description: 'Font resources', critical: false },
    { file: 'openscad.mcad.js', description: 'MCAD library', critical: false }
  ];
  
  const validationResults = [];
  let validAssets = 0;
  let criticalIssues = 0;
  
  for (const asset of expectedWasmFiles) {
    const filePath = path.join(wasmDir, asset.file);
    const result = await checkFileExists(filePath, asset.description);
    
    validationResults.push({
      ...asset,
      ...result
    });
    
    if (result.exists) {
      console.log(`   ✅ ${asset.file}: ${result.sizeFormatted}`);
      validAssets++;
    } else {
      const severity = asset.critical ? '❌' : '⚠️';
      console.log(`   ${severity} ${asset.file}: Missing ${asset.critical ? '(CRITICAL)' : '(optional)'}`);
      if (asset.critical) criticalIssues++;
    }
  }
  
  console.log(`   📊 Valid assets: ${validAssets}/${expectedWasmFiles.length}`);
  if (criticalIssues > 0) {
    console.log(`   🚨 Critical issues: ${criticalIssues}`);
  }
  
  return {
    total: expectedWasmFiles.length,
    valid: validAssets,
    critical_issues: criticalIssues,
    results: validationResults
  };
}

async function validateCompressedAssets(distDir) {
  console.log('\n🔍 Validating compressed assets...');
  
  const compressionTests = [
    { pattern: '*.js.gz', description: 'Compressed JavaScript modules' },
    { pattern: 'wasm/*.wasm.gz', description: 'Compressed WASM binaries' },
    { pattern: 'wasm/*.js.gz', description: 'Compressed WASM JavaScript' }
  ];
  
  let totalCompressed = 0;
  const compressionResults = [];
  
  for (const test of compressionTests) {
    try {
      const files = [];
      
      if (test.pattern.includes('wasm/')) {
        const wasmDir = path.join(distDir, 'wasm');
        try {
          const wasmFiles = await fs.readdir(wasmDir);
          const extension = test.pattern.split('.').slice(-2).join('.');
          files.push(...wasmFiles.filter(f => f.endsWith(extension)));
        } catch {
          // WASM directory doesn't exist
        }
      } else {
        const distFiles = await fs.readdir(distDir);
        const extension = test.pattern.slice(1); // Remove *
        files.push(...distFiles.filter(f => f.endsWith(extension)));
      }
      
      compressionResults.push({
        pattern: test.pattern,
        description: test.description,
        count: files.length,
        files
      });
      
      totalCompressed += files.length;
      
      if (files.length > 0) {
        console.log(`   ✅ ${test.description}: ${files.length} files`);
      } else {
        console.log(`   ⚠️ ${test.description}: No compressed files found`);
      }
      
    } catch (error) {
      console.log(`   ❌ ${test.description}: Error checking - ${error.message}`);
    }
  }
  
  console.log(`   📦 Total compressed files: ${totalCompressed}`);
  
  return {
    total_compressed: totalCompressed,
    results: compressionResults
  };
}

async function validateBuildManifests(distDir) {
  console.log('\n🔍 Validating build manifests...');
  
  const expectedManifests = [
    { file: 'optimization-manifest.json', description: 'Asset optimization manifest' },
    { file: 'nginx-wasm.conf', description: 'Nginx configuration' }
  ];
  
  const manifestResults = [];
  let validManifests = 0;
  
  for (const manifest of expectedManifests) {
    const filePath = path.join(distDir, manifest.file);
    const result = await checkFileExists(filePath, manifest.description);
    
    manifestResults.push({
      ...manifest,
      ...result
    });
    
    if (result.exists) {
      console.log(`   ✅ ${manifest.file}: ${result.sizeFormatted}`);
      validManifests++;
      
      // Validate JSON manifests
      if (manifest.file.endsWith('.json')) {
        try {
          const content = await fs.readFile(filePath, 'utf-8');
          const parsed = JSON.parse(content);
          console.log(`      📄 Valid JSON structure with ${Object.keys(parsed).length} top-level keys`);
        } catch (error) {
          console.log(`      ❌ Invalid JSON: ${error.message}`);
        }
      }
    } else {
      console.log(`   ❌ ${manifest.file}: Missing`);
    }
  }
  
  console.log(`   📊 Valid manifests: ${validManifests}/${expectedManifests.length}`);
  
  return {
    total: expectedManifests.length,
    valid: validManifests,
    results: manifestResults
  };
}

async function generateBuildReport(distDir, validationResults) {
  console.log('\n📄 Generating build verification report...');
  
  const report = {
    timestamp: new Date().toISOString(),
    build_verification: {
      status: 'unknown',
      overall_score: 0,
      critical_issues: 0
    },
    javascript_modules: validationResults.jsModules,
    wasm_assets: validationResults.wasmAssets,
    compressed_assets: validationResults.compressedAssets,
    build_manifests: validationResults.buildManifests,
    summary: {
      total_files_expected: 0,
      total_files_found: 0,
      compression_enabled: validationResults.compressedAssets.total_compressed > 0,
      production_ready: false
    }
  };
  
  // Calculate overall metrics
  report.summary.total_files_expected = 
    validationResults.jsModules.total + 
    validationResults.wasmAssets.total + 
    validationResults.buildManifests.total;
    
  report.summary.total_files_found = 
    validationResults.jsModules.valid + 
    validationResults.wasmAssets.valid + 
    validationResults.buildManifests.valid;
  
  report.build_verification.critical_issues = validationResults.wasmAssets.critical_issues || 0;
  report.build_verification.overall_score = (report.summary.total_files_found / report.summary.total_files_expected) * 100;
  
  // Determine status
  if (report.build_verification.critical_issues > 0) {
    report.build_verification.status = 'failed';
  } else if (report.build_verification.overall_score >= 90) {
    report.build_verification.status = 'excellent';
  } else if (report.build_verification.overall_score >= 75) {
    report.build_verification.status = 'good';
  } else {
    report.build_verification.status = 'needs_improvement';
  }
  
  report.summary.production_ready = 
    report.build_verification.status === 'excellent' && 
    report.summary.compression_enabled;
  
  const reportPath = path.join(distDir, 'build-verification-report.json');
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
  
  console.log(`   ✅ Report saved: ${reportPath}`);
  return report;
}

async function main() {
  const projectRoot = path.resolve(__dirname, '..');
  const distDir = path.join(projectRoot, 'dist');
  
  console.log('🔍 WASM Build Verification');
  console.log('==========================');
  console.log(`📁 Verifying: ${distDir}`);
  console.log('');

  // Check if dist directory exists
  try {
    await fs.access(distDir);
  } catch {
    console.log('❌ Distribution directory not found');
    console.log('   Run `npm run build` first to create the dist directory');
    process.exit(1);
  }

  // Run all validations
  const jsModules = await validateJavaScriptModules(distDir);
  const wasmAssets = await validateWasmAssets(distDir);
  const compressedAssets = await validateCompressedAssets(distDir);
  const buildManifests = await validateBuildManifests(distDir);
  
  // Generate comprehensive report
  const report = await generateBuildReport(distDir, {
    jsModules,
    wasmAssets,
    compressedAssets,
    buildManifests
  });
  
  // Final summary
  console.log('\n📊 Build Verification Summary');
  console.log('=============================');
  console.log(`Overall Score: ${report.build_verification.overall_score.toFixed(1)}%`);
  console.log(`Status: ${report.build_verification.status.toUpperCase()}`);
  console.log(`Files Found: ${report.summary.total_files_found}/${report.summary.total_files_expected}`);
  console.log(`Critical Issues: ${report.build_verification.critical_issues}`);
  console.log(`Compression: ${report.summary.compression_enabled ? 'Enabled' : 'Disabled'}`);
  console.log(`Production Ready: ${report.summary.production_ready ? 'Yes' : 'No'}`);
  
  // Exit with appropriate code
  if (report.build_verification.critical_issues > 0) {
    console.log('\n❌ Build verification failed due to critical issues');
    process.exit(1);
  } else if (report.build_verification.overall_score < 75) {
    console.log('\n⚠️ Build verification shows issues - review the report');
    process.exit(1);
  } else {
    console.log('\n✅ Build verification successful!');
    if (report.summary.production_ready) {
      console.log('🚀 Ready for production deployment');
    }
    process.exit(0);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('❌ Verification failed:', error);
    process.exit(1);
  });
}

export { main as verifyWasmBuild };