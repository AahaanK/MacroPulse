import type { Config } from "tailwindcss";

/**
 * MacroPulse design tokens.
 *
 * The default Tailwind palette is disabled: only the six brand colours (and tints of them)
 * are available.
 *   palladian       #EEE9DF  Ivory       – reading surfaces
 *   oatmeal         #C9C1B1  Oatmeal     – borders, quiet text
 *   blue-fantastic  #2C3B4D  Navy        – primary text accents, primary buttons (light)
 *   burning-flame   #FFB162  Orange      – the single call to action, positive values (dark)
 *   truffle         #A35139  Terracotta  – negative values, warnings
 *   abyssal         #1B2632  Deep navy   – dark sections, body text
 */
const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    colors: {
      transparent: "transparent",
      current: "currentColor",
      palladian: {
        DEFAULT: "#EEE9DF",
        light: "#F8F5F0",
        dark: "#E4DDCF",
      },
      oatmeal: {
        DEFAULT: "#C9C1B1",
        light: "#DBD5CA",
        dark: "#6E6555", // deepened oatmeal: secondary text on ivory (4.6:1)
        muted: "rgba(201, 193, 177, 0.35)",
      },
      "blue-fantastic": {
        DEFAULT: "#2C3B4D",
        light: "#3A4D64",
        dark: "#212D3B",
        muted: "rgba(44, 59, 77, 0.4)",
      },
      "burning-flame": {
        DEFAULT: "#FFB162",
        light: "#FFC488",
        dark: "#E69B4D",
        muted: "rgba(255, 177, 98, 0.25)",
      },
      truffle: {
        DEFAULT: "#A35139",
        light: "#B8644C",
        dark: "#853D28",
        soft: "#D69580", // terracotta tint, readable on deep navy
        muted: "rgba(163, 81, 57, 0.25)",
      },
      abyssal: {
        DEFAULT: "#1B2632",
        light: "#263546",
        mid: "#212E3C", // raised surface on deep navy
        dark: "#131C25",
        muted: "rgba(27, 38, 50, 0.5)",
      },
    },
    extend: {
      fontFamily: {
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        serif: ["'IBM Plex Serif'", "Georgia", "serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
      borderRadius: {
        DEFAULT: "4px",
        md: "6px",
        lg: "8px",
      },
      transitionDuration: {
        DEFAULT: "150ms",
      },
      maxWidth: {
        page: "84rem",
      },
    },
  },
  plugins: [],
};

export default config;
