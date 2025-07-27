import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    watch: {
      usePolling: true,
    },
    hmr: {
      host: "0.0.0.0",
      port: 3000,
      protocol: "ws",
      clientPort: 3000,
    },
    fs: {
      strict: false,
    },
  },
  cacheDir: 'node_modules/.vite/custom_cache_dir',
  build: {
    force: true,
  },
});
