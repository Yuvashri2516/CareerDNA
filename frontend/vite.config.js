import { defineConfig } from 'vite';

export default defineConfig({
  // index.html is at frontend/ root
  root: '.',
  // Assets in public/ are copied as-is to dist/
  publicDir: 'public',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  // Expose VITE_ env vars to the browser
  envPrefix: 'VITE_',
});
