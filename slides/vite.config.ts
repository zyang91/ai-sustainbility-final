import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" so the built deck works from any folder, including GitHub Pages
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: { port: 8521 },
});
