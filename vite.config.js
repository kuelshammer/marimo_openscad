import { defineConfig } from 'vite';

export default defineConfig({
  // Build configuration for JavaScript widget development with WASM support
  build: {
    lib: {
      entry: {
        widget: 'src/js/widget.js',
        'wasm-loader': 'src/js/wasm-loader.js',
        'wasm-renderer': 'src/js/openscad-wasm-renderer.js',
        'worker-manager': 'src/js/worker-manager.js',
        'memory-manager': 'src/js/memory-manager.js',
        'cache-manager': 'src/js/wasm-cache-manager.js',
        'openscad-worker': 'src/js/openscad-worker.js'
      },
      name: 'MarimoOpenSCADWidget',
      fileName: (format, entryName) => `${entryName}.${format}.js`,
      formats: ['es', 'umd']
    },
    rollupOptions: {
      external: ['three'],
      output: {
        globals: {
          three: 'THREE'
        },
        // Preserve dynamic imports for WASM modules
        preserveEntrySignatures: 'strict',
        // Handle WASM files properly
        assetFileNames: (assetInfo) => {
          if (assetInfo.name.endsWith('.wasm')) {
            return 'wasm/[name][extname]';
          }
          return 'assets/[name].[hash][extname]';
        }
      }
    },
    outDir: 'dist',
    sourcemap: true,
    target: 'es2020', // Required for WASM and modern features
    
    // WASM-specific optimizations
    assetsInlineLimit: 0, // Don't inline WASM files
    
    // Ensure WASM files are copied properly
    copyPublicDir: true
  },
  
  // Development server configuration with WASM support
  server: {
    port: 3000,
    open: true,
    host: true,
    headers: {
      // Required for WASM in development
      'Cross-Origin-Embedder-Policy': 'require-corp',
      'Cross-Origin-Opener-Policy': 'same-origin'
    },
    // Handle WASM file serving
    middlewareMode: false,
    fs: {
      allow: ['..'] // Allow serving files from parent directories
    }
  },
  
  // Worker configuration for WASM workers
  worker: {
    format: 'es',
    plugins: []
  },
  
  // Optimizations for WASM development
  optimizeDeps: {
    exclude: ['*.wasm'], // Don't pre-bundle WASM files
    include: ['three'] // Pre-bundle Three.js for faster dev
  },
  
  // Test configuration
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['src/test/setup.js']
  },
  
  // Base directory for assets
  base: './',
  
  // Public directory for static assets
  publicDir: 'public'
});