import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    name: 'WASM Integration Tests',
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['src/test/setup.js', 'src/test/wasm-test-fixtures.js'],
    
    // WASM-specific test configuration
    testMatch: [
      '**/*.wasm.test.{js,ts}',
      '**/test-wasm-*.{js,ts}',
      'src/test/wasm-*.{js,ts}'
    ],
    
    // Longer timeout for WASM loading
    testTimeout: 10000,
    hookTimeout: 10000,
    
    // Coverage configuration for WASM files
    coverage: {
      provider: 'v8',
      include: [
        'src/js/wasm-*.js',
        'src/js/*-wasm-*.js',
        'src/js/memory-manager.js',
        'src/js/worker-manager.js'
      ],
      exclude: [
        'src/js/openscad-worker.js', // Worker context
        'node_modules/**',
        'dist/**'
      ],
      reporter: ['text', 'json', 'html']
    },
    
    // Environment variables for WASM testing
    env: {
      WASM_TEST_MODE: 'true',
      NODE_ENV: 'test'
    },
    
    // Browser-like environment for WASM
    define: {
      'typeof window': '"object"',
      'typeof Worker': '"function"',
      'typeof WebAssembly': '"object"'
    }
  },
  
  // Build configuration for WASM tests
  esbuild: {
    target: 'es2020' // Required for WASM support
  },
  
  // Dependencies handling
  optimizeDeps: {
    include: ['three'],
    exclude: ['*.wasm']
  }
});