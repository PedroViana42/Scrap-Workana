import { defineConfig } from "vitest/config";
import path from "node:path";

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["app/**/*.{test,spec}.{ts,tsx}", "components/**/*.{test,spec}.{ts,tsx}", "lib/**/*.{test,spec}.{ts,tsx}"],
    exclude: ["node_modules/**", "node_modules.partial.*/**", ".next/**"],
    setupFiles: ["./vitest.setup.ts"],
  },
});
