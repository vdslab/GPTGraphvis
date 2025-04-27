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
      // HMRの設定を追加
      host: 'localhost',
      port: 3000,
      protocol: 'ws',
      clientPort: 3000 // クライアント側のポート
    },
    // Removed proxy configuration as we're connecting directly to the API
  },
});
