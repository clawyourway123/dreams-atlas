import type { Config } from "tailwindcss";

/**
 * DREAMS Atlas — Tailwind CSS Design System
 * K-Dense Science Lab Brand Identity
 *
 * Color palette extracted from K-Dense Investor Pitch Deck
 * to ensure brand consistency across all digital properties.
 */
const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      /* ──────────────── Colors ──────────────── */
      colors: {
        // Primary — Dark Navy (from pitch deck backgrounds)
        navy: {
          50: "#f0f4f8",
          100: "#d9e2ec",
          200: "#bcccdc",
          300: "#9fb3c8",
          400: "#829ab1",
          500: "#627d98",
          600: "#486581",
          700: "#334e68",
          800: "#243b53",
          900: "#1e293b", // Main background color from pitch deck
          950: "#171f2e", // Deeper variant for contrast
        },

        // Accent — Teal/Emerald (from pitch deck dividers, CTAs, table headers)
        teal: {
          50: "#effcf6",
          100: "#c6f7de",
          200: "#8eedd0",
          300: "#5be0be",
          400: "#2dd4bf", // Primary accent — matches pitch deck highlight bar
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
          900: "#134e4a",
          950: "#042f2e",
        },

        // Surface — Slightly lighter navy for cards, panels
        surface: {
          DEFAULT: "#243b53",
          light: "#2d4a63",
          lighter: "#365d78",
          dark: "#1a2d42",
        },

        // Semantic colors
        success: "#22c55e",
        warning: "#f59e0b",
        error: "#ef4444",
        info: "#3b82f6",
      },

      /* ──────────────── Typography ──────────────── */
      fontFamily: {
        // Primary — Clean geometric sans for headings (matches pitch deck)
        heading: [
          "Inter",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        // Body — Optimized for readability at small sizes
        body: [
          "Inter",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        // Mono — For spectral data, code, metrics
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "SF Mono",
          "Consolas",
          "monospace",
        ],
      },

      fontSize: {
        // Display sizes for hero sections
        "display-xl": ["4.5rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-lg": ["3.75rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-md": ["3rem", { lineHeight: "1.15", letterSpacing: "-0.01em" }],
        // Section headings
        "heading-xl": ["2.25rem", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
        "heading-lg": ["1.875rem", { lineHeight: "1.25" }],
        "heading-md": ["1.5rem", { lineHeight: "1.3" }],
        "heading-sm": ["1.25rem", { lineHeight: "1.35" }],
        // Body text
        "body-lg": ["1.125rem", { lineHeight: "1.6" }],
        "body-md": ["1rem", { lineHeight: "1.6" }],
        "body-sm": ["0.875rem", { lineHeight: "1.5" }],
        // Captions and labels
        caption: ["0.75rem", { lineHeight: "1.4", letterSpacing: "0.02em" }],
        overline: [
          "0.75rem",
          { lineHeight: "1.4", letterSpacing: "0.08em", fontWeight: "600" },
        ],
      },

      /* ──────────────── Spacing & Layout ──────────────── */
      spacing: {
        18: "4.5rem",
        22: "5.5rem",
        30: "7.5rem",
        34: "8.5rem",
        // Section spacing
        "section-sm": "4rem",
        "section-md": "6rem",
        "section-lg": "8rem",
      },

      maxWidth: {
        "content-narrow": "42rem",
        "content-default": "64rem",
        "content-wide": "80rem",
        "content-full": "90rem",
      },

      /* ──────────────── Effects ──────────────── */
      borderRadius: {
        "2xs": "0.125rem",
        xs: "0.25rem",
        card: "0.75rem",
        panel: "1rem",
        pill: "9999px",
      },

      boxShadow: {
        card: "0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.2)",
        "card-hover":
          "0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -4px rgba(0, 0, 0, 0.3)",
        glow: "0 0 20px rgba(45, 212, 191, 0.15)",
        "glow-strong": "0 0 40px rgba(45, 212, 191, 0.25)",
        "inner-light": "inset 0 1px 0 0 rgba(255, 255, 255, 0.05)",
      },

      /* ──────────────── Animations ──────────────── */
      animation: {
        "fade-in": "fadeIn 0.6s ease-out",
        "fade-in-up": "fadeInUp 0.6s ease-out",
        "slide-in-left": "slideInLeft 0.6s ease-out",
        "slide-in-right": "slideInRight 0.6s ease-out",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "count-up": "countUp 1.5s ease-out",
      },

      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInLeft: {
          "0%": { opacity: "0", transform: "translateX(-30px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(30px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 20px rgba(45, 212, 191, 0.15)" },
          "50%": { boxShadow: "0 0 40px rgba(45, 212, 191, 0.3)" },
        },
      },

      /* ──────────────── Backdrop ──────────────── */
      backdropBlur: {
        xs: "2px",
      },

      /* ──────────────── Background patterns ──────────────── */
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "hero-gradient":
          "linear-gradient(135deg, #1e293b 0%, #243b53 50%, #1a2d42 100%)",
        "card-gradient":
          "linear-gradient(180deg, rgba(45, 212, 191, 0.05) 0%, transparent 100%)",
        "teal-gradient":
          "linear-gradient(135deg, #14b8a6 0%, #2dd4bf 100%)",
        "section-gradient":
          "linear-gradient(180deg, #171f2e 0%, #1e293b 50%, #171f2e 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
