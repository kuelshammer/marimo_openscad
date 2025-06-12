export default [
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        THREE: 'readonly',
        console: 'readonly',
        window: 'readonly',
        document: 'readonly',
        fetch: 'readonly',
        URL: 'readonly',
        Blob: 'readonly',
        Worker: 'readonly',
        WebAssembly: 'readonly',
        performance: 'readonly',
        requestAnimationFrame: 'readonly',
        atob: 'readonly',
        btoa: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        Promise: 'readonly',
        Map: 'readonly',
        Set: 'readonly',
        Array: 'readonly',
        Object: 'readonly',
        Date: 'readonly',
        Math: 'readonly',
        parseInt: 'readonly',
        parseFloat: 'readonly',
        self: 'readonly',
        importScripts: 'readonly',
        DataView: 'readonly',
        Uint8Array: 'readonly',
        ArrayBuffer: 'readonly',
        Float32Array: 'readonly',
        caches: 'readonly',
        Cache: 'readonly',
        Request: 'readonly',
        Response: 'readonly'
      }
    },
    rules: {
      'indent': ['error', 4],
      'linebreak-style': ['error', 'unix'],
      'quotes': ['error', 'single'],
      'semi': ['error', 'always'],
      'no-unused-vars': ['warn'],
      'no-console': 'off',
      'prefer-const': 'error',
      'no-var': 'error',
    }
  },
  {
    files: ['**/*.test.js', '**/*.spec.js'],
    languageOptions: {
      globals: {
        describe: 'readonly',
        it: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        vi: 'readonly',
        test: 'readonly'
      }
    }
  }
];