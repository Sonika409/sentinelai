import type { Config } from "tailwindcss"

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sentinel: {
          bg:      "#0a0a0f",
          surface: "#111118",
          border:  "#1e1e2e",
          green:   "#00ff88",
          cyan:    "#00d4ff",
          red:     "#ff3366",
          yellow:  "#ffb800",
          purple:  "#a855f7",
          muted:   "#64748b",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      animation: {
        blink: "blink 1s step-end infinite",
        "slide-in": "slideIn 0.3s ease-out",
        "fade-in": "fadeIn 0.4s ease-out",
      },
      keyframes: {
        blink:   { "0%,100%": { opacity: "1" }, "50%": { opacity: "0" } },
        slideIn: { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        fadeIn:  { from: { opacity: "0" }, to: { opacity: "1" } },
      },
    },
  },
  plugins: [],
}

export default config
