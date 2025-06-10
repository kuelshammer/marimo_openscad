import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Test environment - happy-dom provides DOM APIs for testing
    environment: 'happy-dom',
    
    // Global test APIs (describe, it, expect, etc.)
    globals: true,
    
    // Setup files to run before tests
    setupFiles: ['src/test/setup.js'],
    
    // Include/exclude patterns
    include: ['src/test/**/*.{test,spec}.{js,ts}'],
    exclude: ['node_modules', 'dist'],
    
    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['src/js/**/*.js'],
      exclude: ['src/test/**']
    },
    
    // Test timeout
    testTimeout: 10000,
    
    // Watch mode options
    watch: {
      include: ['src/**/*.js']
    }
  }
});