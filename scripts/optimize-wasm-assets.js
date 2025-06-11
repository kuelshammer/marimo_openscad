#!/usr/bin/env node
/**
 * Optimize WASM Assets for Production
 * 
 * This script optimizes WASM files and JavaScript modules
 * for production deployment, including compression and CDN preparation.
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { createGzip } from 'zlib';
import { promisify } from 'util';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const gzip = promisify(createGzip);

async function ensureDirectory(dirPath) {
  try {
    await fs.access(dirPath);
  } catch {
    await fs.mkdir(dirPath, { recursive: true });
    console.log(`📁 Created directory: ${dirPath}`);
  }
}

async function getFileSize(filePath) {
  try {
    const stats = await fs.stat(filePath);
    return stats.size;
  } catch {
    return 0;
  }
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
}

async function compressFile(inputPath, outputPath) {
  try {
    const inputBuffer = await fs.readFile(inputPath);
    const compressedBuffer = await new Promise((resolve, reject) => {
      const gzip = createGzip({ level: 9 }); // Maximum compression
      const chunks = [];
      
      gzip.on('data', chunk => chunks.push(chunk));
      gzip.on('end', () => resolve(Buffer.concat(chunks)));
      gzip.on('error', reject);
      
      gzip.end(inputBuffer);
    });
    
    await fs.writeFile(outputPath, compressedBuffer);
    
    const originalSize = inputBuffer.length;
    const compressedSize = compressedBuffer.length;
    const compressionRatio = ((originalSize - compressedSize) / originalSize * 100);
    
    return {
      originalSize,
      compressedSize,
      compressionRatio,
      success: true
    };
  } catch (error) {
    return {
      error: error.message,
      success: false
    };
  }
}

async function optimizeJavaScriptModules(distDir) {
  console.log('\n🔧 Optimizing JavaScript modules...');
  
  const jsFiles = [];
  
  try {
    const files = await fs.readdir(distDir);
    for (const file of files) {
      if (file.endsWith('.js') || file.endsWith('.mjs')) {
        jsFiles.push(file);
      }
    }
  } catch (error) {
    console.log(`   ⚠️ Could not read dist directory: ${error.message}`);
    return [];
  }
  
  const optimizationResults = [];
  
  for (const jsFile of jsFiles) {
    const inputPath = path.join(distDir, jsFile);
    const outputPath = path.join(distDir, `${jsFile}.gz`);
    
    console.log(`   📦 Compressing: ${jsFile}`);
    
    const result = await compressFile(inputPath, outputPath);
    
    if (result.success) {
      console.log(`      ✅ ${formatFileSize(result.originalSize)} → ${formatFileSize(result.compressedSize)} (${result.compressionRatio.toFixed(1)}% smaller)`);
      optimizationResults.push({
        file: jsFile,
        ...result
      });
    } else {
      console.log(`      ❌ Failed: ${result.error}`);
    }
  }
  
  return optimizationResults;
}

async function optimizeWasmFiles(wasmDir, distDir) {
  console.log('\n🔧 Optimizing WASM files...');
  
  const wasmFiles = [];
  
  try {
    const files = await fs.readdir(wasmDir);
    for (const file of files) {
      if (file.endsWith('.wasm') || file.endsWith('.js')) {
        wasmFiles.push(file);
      }
    }
  } catch (error) {
    console.log(`   ⚠️ Could not read WASM directory: ${error.message}`);
    return [];
  }
  
  // Ensure dist/wasm directory exists
  const distWasmDir = path.join(distDir, 'wasm');
  await ensureDirectory(distWasmDir);
  
  const optimizationResults = [];
  
  for (const wasmFile of wasmFiles) {
    const inputPath = path.join(wasmDir, wasmFile);
    const copyPath = path.join(distWasmDir, wasmFile);
    const compressedPath = path.join(distWasmDir, `${wasmFile}.gz`);
    
    console.log(`   📦 Processing: ${wasmFile}`);
    
    // Copy original file to dist
    try {
      await fs.copyFile(inputPath, copyPath);
      console.log(`      📄 Copied to dist/wasm/`);
    } catch (error) {
      console.log(`      ❌ Copy failed: ${error.message}`);
      continue;
    }
    
    // Compress file
    const result = await compressFile(inputPath, compressedPath);
    
    if (result.success) {
      console.log(`      ✅ ${formatFileSize(result.originalSize)} → ${formatFileSize(result.compressedSize)} (${result.compressionRatio.toFixed(1)}% smaller)`);
      optimizationResults.push({
        file: wasmFile,
        ...result
      });
    } else {
      console.log(`      ❌ Compression failed: ${result.error}`);
    }
  }
  
  return optimizationResults;
}

async function generateCacheManifest(distDir, jsResults, wasmResults) {
  console.log('\n📄 Generating cache manifest...');
  
  const manifest = {
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    cache_strategy: {
      js_modules: '7 days',
      wasm_modules: '30 days',
      compression: 'gzip'
    },
    files: {
      javascript: jsResults.map(result => ({
        name: result.file,
        original_size: result.originalSize,
        compressed_size: result.compressedSize,
        compression_ratio: result.compressionRatio,
        cache_headers: {
          'Cache-Control': 'public, max-age=604800', // 7 days
          'Content-Encoding': 'gzip',
          'Content-Type': 'application/javascript'
        }
      })),
      wasm: wasmResults.map(result => ({
        name: result.file,
        original_size: result.originalSize,
        compressed_size: result.compressedSize,
        compression_ratio: result.compressionRatio,
        cache_headers: result.file.endsWith('.wasm') ? {
          'Cache-Control': 'public, max-age=2592000', // 30 days
          'Content-Encoding': 'gzip',
          'Content-Type': 'application/wasm'
        } : {
          'Cache-Control': 'public, max-age=2592000', // 30 days
          'Content-Encoding': 'gzip',
          'Content-Type': 'application/javascript'
        }
      }))
    },
    statistics: {
      total_files: jsResults.length + wasmResults.length,
      total_original_size: [...jsResults, ...wasmResults].reduce((sum, r) => sum + r.originalSize, 0),
      total_compressed_size: [...jsResults, ...wasmResults].reduce((sum, r) => sum + r.compressedSize, 0),
      average_compression_ratio: [...jsResults, ...wasmResults].reduce((sum, r) => sum + r.compressionRatio, 0) / (jsResults.length + wasmResults.length)
    }
  };
  
  const manifestPath = path.join(distDir, 'optimization-manifest.json');
  await fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2));
  
  console.log(`   ✅ Cache manifest created: ${manifestPath}`);
  return manifest;
}

async function generateNginxConfig(distDir, manifest) {
  console.log('\n🌐 Generating Nginx configuration...');
  
  const nginxConfig = `# Nginx configuration for marimo-openscad WASM assets
# Add this to your server block

# WASM files - long cache, compression
location ~* \\.wasm$ {
    add_header Cache-Control "public, max-age=2592000"; # 30 days
    add_header Content-Encoding gzip;
    gzip_static on;
    expires 30d;
}

# JavaScript modules - medium cache, compression  
location ~* \\.(js|mjs)$ {
    add_header Cache-Control "public, max-age=604800"; # 7 days
    add_header Content-Encoding gzip;
    gzip_static on;
    expires 7d;
}

# WASM module loader files
location /wasm/ {
    add_header Cache-Control "public, max-age=2592000";
    add_header Access-Control-Allow-Origin "*";
    add_header Access-Control-Allow-Methods "GET";
    gzip_static on;
}

# Security headers for WASM
location / {
    add_header Cross-Origin-Embedder-Policy "require-corp";
    add_header Cross-Origin-Opener-Policy "same-origin";
}

# Compression settings
gzip on;
gzip_vary on;
gzip_types
    application/javascript
    application/wasm
    text/css
    text/xml
    text/plain;
`;
  
  const configPath = path.join(distDir, 'nginx-wasm.conf');
  await fs.writeFile(configPath, nginxConfig);
  
  console.log(`   ✅ Nginx config created: ${configPath}`);
  return configPath;
}

async function main() {
  const projectRoot = path.resolve(__dirname, '..');
  const distDir = path.join(projectRoot, 'dist');
  const wasmDir = path.join(projectRoot, 'public', 'wasm');
  
  console.log('⚡ WASM Asset Optimizer');
  console.log('======================');
  console.log(`📁 Distribution directory: ${distDir}`);
  console.log(`📁 WASM source directory: ${wasmDir}`);
  console.log('');

  // Check if dist directory exists
  try {
    await fs.access(distDir);
  } catch {
    console.log('❌ Distribution directory not found');
    console.log('   Run `npm run build` first to create the dist directory');
    process.exit(1);
  }

  // Optimize JavaScript modules
  const jsResults = await optimizeJavaScriptModules(distDir);
  
  // Optimize WASM files
  const wasmResults = await optimizeWasmFiles(wasmDir, distDir);
  
  // Generate cache manifest
  const manifest = await generateCacheManifest(distDir, jsResults, wasmResults);
  
  // Generate Nginx configuration
  await generateNginxConfig(distDir, manifest);
  
  // Summary
  console.log('\n📊 Optimization Summary');
  console.log('======================');
  console.log(`JavaScript files: ${jsResults.length}`);
  console.log(`WASM files: ${wasmResults.length}`);
  console.log(`Total original size: ${formatFileSize(manifest.statistics.total_original_size)}`);
  console.log(`Total compressed size: ${formatFileSize(manifest.statistics.total_compressed_size)}`);
  console.log(`Average compression: ${manifest.statistics.average_compression_ratio.toFixed(1)}%`);
  console.log('');
  console.log('🎉 Assets optimized for production deployment!');
  console.log('');
  console.log('📁 Generated files:');
  console.log('   - Compressed .gz versions of all assets');
  console.log('   - optimization-manifest.json (cache configuration)');
  console.log('   - nginx-wasm.conf (web server configuration)');
  console.log('   - dist/wasm/ (WASM modules for CDN)');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('❌ Optimization failed:', error);
    process.exit(1);
  });
}

export { main as optimizeWasmAssets };