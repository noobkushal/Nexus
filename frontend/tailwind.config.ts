import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        nexus: {
          950: "#07090e",
          900: "#0d1117",
          850: "#131720",
          800: "#161b22",
          700: "#21262d",
          600: "#30363d",
          500: "#484f58",
          400: "#8b949e",
          300: "#b1bac4",
          200: "#c9d1d9",
          100: "#f0f6fc",
        },
        accent: {
          cyan: "#00e5ff",
          indigo: "#6366f1",
          emerald: "#10b981",
          amber: "#f59e0b",
        },
      },
    },
  },
  plugins: [],
};
export default config;
