#!/usr/bin/env node
/**
 * Download and setup OpenSCAD WASM modules
 * 
 * This script downloads the official OpenSCAD WASM modules
 * and sets them up for the build process.
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const OPENSCAD_WASM_VERSION = '2022.03.20';
const WASM_BASE_URL = `https://files.openscad.org/wasm/${OPENSCAD_WASM_VERSION}`;

const WASM_FILES = [
  'openscad.js',
  'openscad.wasm',
  'openscad.wasm.js',
  'openscad.d.ts',
  'openscad.fonts.js',
  'openscad.fonts.d.ts',
  'openscad.mcad.js',
  'openscad.mcad.d.ts'
];

async function ensureDirectory(dirPath) {
  try {
    await fs.access(dirPath);
  } catch {
    await fs.mkdir(dirPath, { recursive: true });
    console.log(`📁 Created directory: ${dirPath}`);
  }
}

async function downloadFile(url, outputPath) {
  console.log(`📥 Downloading: ${path.basename(outputPath)}`);
  
  try {
    // Check if file already exists
    const stats = await fs.stat(outputPath);
    if (stats.size > 0) {
      console.log(`   ✅ File already exists: ${path.basename(outputPath)}`);
      return true;
    }
  } catch {
    // File doesn't exist, proceed with download
  }

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const buffer = await response.arrayBuffer();
    await fs.writeFile(outputPath, Buffer.from(buffer));
    
    console.log(`   ✅ Downloaded: ${path.basename(outputPath)} (${(buffer.byteLength / 1024 / 1024).toFixed(2)} MB)`);
    return true;
  } catch (error) {
    console.error(`   ❌ Failed to download ${path.basename(outputPath)}: ${error.message}`);
    return false;
  }
}

async function verifyWasmFiles(wasmDir) {
  console.log('\n🔍 Verifying WASM files...');
  
  const verificationResults = {};
  
  for (const filename of WASM_FILES) {
    const filePath = path.join(wasmDir, filename);
    
    try {
      const stats = await fs.stat(filePath);
      verificationResults[filename] = {
        exists: true,
        size: stats.size,
        sizeFormatted: (stats.size / 1024 / 1024).toFixed(2) + ' MB'
      };
      console.log(`   ✅ ${filename}: ${verificationResults[filename].sizeFormatted}`);
    } catch {
      verificationResults[filename] = { exists: false };
      console.log(`   ❌ ${filename}: Missing`);
    }
  }
  
  return verificationResults;
}

async function createWasmManifest(wasmDir, verificationResults) {
  const manifest = {
    version: OPENSCAD_WASM_VERSION,
    timestamp: new Date().toISOString(),
    base_url: WASM_BASE_URL,
    files: verificationResults,
    integrity: {
      verified: Object.values(verificationResults).every(file => file.exists),
      total_files: WASM_FILES.length,
      downloaded_files: Object.values(verificationResults).filter(file => file.exists).length
    }
  };
  
  const manifestPath = path.join(wasmDir, 'manifest.json');
  await fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2));
  
  console.log(`📄 Created manifest: ${manifestPath}`);
  return manifest;
}

async function main() {
  const projectRoot = path.resolve(__dirname, '..');
  const wasmDir = path.join(projectRoot, 'public', 'wasm');
  
  console.log('🚀 OpenSCAD WASM Module Downloader');
  console.log('=====================================');
  console.log(`📁 Target directory: ${wasmDir}`);
  console.log(`🔗 Source: OpenSCAD ${OPENSCAD_WASM_VERSION}`);
  console.log('');

  // Ensure WASM directory exists
  await ensureDirectory(wasmDir);

  // Check if files already exist
  console.log('🔍 Checking existing files...');
  const verificationResults = await verifyWasmFiles(wasmDir);
  
  const existingFiles = Object.entries(verificationResults)
    .filter(([_, info]) => info.exists)
    .length;

  if (existingFiles === WASM_FILES.length) {
    console.log('\n✅ All WASM files already present!');
    await createWasmManifest(wasmDir, verificationResults);
    console.log('\n🎉 WASM modules ready for build process');
    return;
  }

  console.log(`\n📥 Downloading missing files (${WASM_FILES.length - existingFiles} remaining)...`);

  // Download missing files
  const downloadPromises = WASM_FILES.map(async (filename) => {
    if (verificationResults[filename]?.exists) {
      return true; // Skip existing files
    }
    
    const url = `${WASM_BASE_URL}/${filename}`;
    const outputPath = path.join(wasmDir, filename);
    return downloadFile(url, outputPath);
  });

  const downloadResults = await Promise.all(downloadPromises);
  const successfulDownloads = downloadResults.filter(Boolean).length;

  // Verify all files after download
  console.log('\n🔍 Final verification...');
  const finalVerification = await verifyWasmFiles(wasmDir);
  const manifest = await createWasmManifest(wasmDir, finalVerification);

  // Summary
  console.log('\n📊 Download Summary');
  console.log('==================');
  console.log(`Total files: ${WASM_FILES.length}`);
  console.log(`Downloaded: ${successfulDownloads}`);
  console.log(`Verified: ${manifest.integrity.downloaded_files}`);
  console.log(`Status: ${manifest.integrity.verified ? '✅ Complete' : '⚠️ Incomplete'}`);

  if (manifest.integrity.verified) {
    console.log('\n🎉 All WASM modules downloaded and verified!');
    console.log('   Ready for build process');
  } else {
    console.log('\n⚠️ Some files missing - build may fail');
    console.log('   Try running the script again');
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('❌ Download failed:', error);
    process.exit(1);
  });
}

export { main as downloadWasmModules };