#!/usr/bin/env bash
set -euo pipefail

# Install all dependencies including devDependencies (needed for tailwindcss, postcss, autoprefixer at build time)
npm install --include=dev

# Build Next.js
npm run build

# Copy static assets into the standalone output for serving
cp -r public .next/standalone/public 2>/dev/null || true
cp -r .next/static .next/standalone/.next/static
