/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        command: {
          bg: "#090d16",
          panel: "#0f172a",
          card: "#131d31",
          border: "#1e293b",
          borderGlow: "#334155",
          cyan: "#06b6d4",
          emerald: "#10b981",
          amber: "#f59e0b",
          crimson: "#ef4444"
        }
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif']
      }
    },
  },
  plugins: [],
}
