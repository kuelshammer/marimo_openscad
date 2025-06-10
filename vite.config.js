import { defineConfig } from 'vite';

export default defineConfig({
  // Build configuration for JavaScript widget development
  build: {
    lib: {
      entry: 'src/js/widget.js',
      name: 'MarimoOpenSCADWidget',
      fileName: (format) => `widget.${format}.js`,
      formats: ['es', 'umd']
    },
    rollupOptions: {
      external: ['three'],
      output: {
        globals: {
          three: 'THREE'
        }
      }
    },
    outDir: 'dist',
    sourcemap: true
  },
  
  // Development server configuration
  server: {
    port: 3000,
    open: true,
    host: true
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