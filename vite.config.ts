import { defineConfig } from "vite";
import solid from "vite-plugin-solid";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [solid(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "frontend"),
    },
  },
  build: {
    outDir: "dist-frontend",
  },
});
