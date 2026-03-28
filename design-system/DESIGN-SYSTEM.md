# DREAMS Atlas — Visual Design System

**K-Dense Science Lab** | Frontend Design Specifications
Version 1.0 | March 2026

---

## Brand Overview

DREAMS Atlas is the web-facing product of K-Dense Science Lab — an AI-powered spectral classification platform for adhesive identification. The visual identity conveys **scientific credibility**, **technical innovation**, and **enterprise-grade professionalism**.

---

## 1. Color Palette

### Primary — Dark Navy

The foundation of the K-Dense brand. Used for backgrounds, headers, and structural elements.

| Token          | Hex       | Usage                              |
| -------------- | --------- | ---------------------------------- |
| `navy-950`     | `#171f2e` | Page background, deepest surfaces  |
| `navy-900`     | `#1e293b` | Section backgrounds, table headers |
| `navy-800`     | `#243b53` | Card backgrounds, panels           |
| `navy-700`     | `#334e68` | Borders, dividers, subtle elements |
| `navy-600`     | `#486581` | Secondary text, muted elements     |
| `navy-300`     | `#9fb3c8` | Body text on dark backgrounds      |
| `navy-100`     | `#d9e2ec` | Emphasized body text               |

### Accent — Teal

The signature accent color from the pitch deck. Used for CTAs, highlights, interactive elements, and data emphasis.

| Token          | Hex       | Usage                                |
| -------------- | --------- | ------------------------------------ |
| `teal-400`     | `#2dd4bf` | Primary accent, CTA buttons, links   |
| `teal-500`     | `#14b8a6` | Category pills, active states        |
| `teal-600`     | `#0d9488` | Table header backgrounds, hover      |
| `teal-400/10`  | —         | Subtle teal backgrounds, badges      |
| `teal-400/20`  | —         | Border highlights on hover           |

### Surface Colors

| Token            | Hex       | Usage                    |
| ---------------- | --------- | ------------------------ |
| `surface`        | `#243b53` | Default card background  |
| `surface-light`  | `#2d4a63` | Elevated card background |
| `surface-dark`   | `#1a2d42` | Recessed surfaces        |

### Text Colors

| Context              | Color         | Token/Value              |
| -------------------- | ------------- | ------------------------ |
| Headings on dark     | White         | `text-white`             |
| Body on dark         | Light slate   | `text-navy-300`          |
| Muted/captions       | Mid slate     | `text-navy-400`          |
| Accent text          | Teal          | `text-teal-400`          |
| Text on teal buttons | Dark navy     | `text-navy-950`          |

---

## 2. Typography

### Font Stack

- **Headings & UI**: `Inter` (or system sans-serif fallback)
- **Body**: `Inter` — optimized for screen readability
- **Monospace**: `JetBrains Mono` — for spectral data, metrics, code

### Type Scale

| Token          | Size    | Weight    | Usage                            |
| -------------- | ------- | --------- | -------------------------------- |
| `display-xl`   | 4.5rem  | Bold      | Hero headline                    |
| `display-lg`   | 3.75rem | Bold      | Hero headline (mobile-first)     |
| `display-md`   | 3rem    | Bold      | Section titles, CTA banners      |
| `heading-xl`   | 2.25rem | Bold      | Section headings                 |
| `heading-lg`   | 1.875rem| Bold      | Subsection headings              |
| `heading-md`   | 1.5rem  | Semibold  | Card titles, feature names       |
| `heading-sm`   | 1.25rem | Semibold  | Small card titles, nav items     |
| `body-lg`      | 1.125rem| Regular   | Hero subtitle, lead paragraphs   |
| `body-md`      | 1rem    | Regular   | Default body text                |
| `body-sm`      | 0.875rem| Regular   | Table cells, captions, nav links |
| `overline`     | 0.75rem | Semibold  | Section labels, UPPERCASE        |
| `caption`      | 0.75rem | Regular   | Fine print, axis labels          |

---

## 3. Component Specifications

### 3.1 Navigation Bar

```
┌──────────────────────────────────────────────────────────────────┐
│  [K] K-Dense          Technology  Data  Pricing  Team    [CTA]  │
│  logo-mark + wordmark       nav-links (hidden < md)     button  │
└──────────────────────────────────────────────────────────────────┘
```

- **Height**: 64px (`h-16`)
- **Background**: `navy-950/80` with `backdrop-blur-md`
- **Position**: Fixed top, `z-50`
- **Border**: Bottom `border-white/5`
- **Logo**: Teal gradient square mark (32x32) + white wordmark
- **Links**: `navy-300` default, `white` on hover, `teal-400` when active
- **CTA**: `btn-primary` style, compact (`py-2 px-5`)

### 3.2 Hero Section

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                    [DREAMS ATLAS badge]                           │
│                                                                  │
│              K-Dense Science Lab                                 │
│    AI-Powered Material Identification                            │
│    Through Spectral Intelligence                                 │
│              ════════════                                        │
│    Classify adhesives into 7 categories                          │
│    in seconds using IR and Raman spectroscopy                    │
│                                                                  │
│         [Try Demo]  [Learn More]                                 │
│                                                                  │
│               bg-grid or bg-dots overlay                         │
└──────────────────────────────────────────────────────────────────┘
```

- **Background**: `hero-gradient` (135deg navy sweep) + `bg-grid` overlay
- **Min height**: `100vh`
- **Badge**: Teal pill with `teal-400/10` bg, `teal-400/20` border
- **Title**: `display-xl` on desktop, `display-lg` on mobile
- **Subtitle**: `body-lg`, `navy-300`, max-width `42rem`
- **Divider**: 96px wide, 4px tall, `teal-gradient`, centered
- **Buttons**: Primary (teal gradient) + Secondary (outline white)

### 3.3 Feature Cards (3-column grid)

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  [icon]         │ │  [icon]         │ │  [icon]         │
│                 │ │                 │ │                 │
│  Feature Title  │ │  Feature Title  │ │  Feature Title  │
│  Description    │ │  Description    │ │  Description    │
│  text here...   │ │  text here...   │ │  text here...   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

- **Grid**: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8`
- **Card**: `surface/60`, `backdrop-blur-sm`, `border-white/5`, `rounded-panel` (16px)
- **Padding**: `p-8`
- **Icon**: 48x48 rounded box, `teal-400/10` bg, teal icon
- **Hover**: Border shifts to `teal-400/20`, shadow strengthens, bg becomes more opaque
- **Shadow**: `shadow-card` default, `shadow-card-hover` on hover

### 3.4 Stats / Metrics Row

```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  95-100% │ │  7       │ │ 1,500+   │ │ Seconds  │
│ Accuracy │ │ Classes  │ │ Spectra  │ │ Per Test │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

- **Grid**: `grid-cols-2 md:grid-cols-4 gap-6`
- **Value**: `display-md`, `teal-400`, bold
- **Label**: `body-sm`, `navy-300`
- **Background**: `surface/40`, `border-white/5`

### 3.5 Team Cards (4-column grid)

```
┌─────────────┐
│    (AV)     │  ← Initials in circle avatar
│  Dr. Name   │
│  Role Title │
│  Description│
└─────────────┘
```

- **Grid**: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6`
- **Avatar**: 80x80 circle, gradient border (`teal-400/30`), teal initials
- **Name**: `heading-sm`, white, bold
- **Role**: `body-sm`, `teal-400`, medium weight
- **Description**: `body-sm`, `navy-300`
- **Hover**: Border becomes `teal-400/20`, bg lightens

### 3.6 Data Tables (Pitch Deck Style)

- **Header row**: `navy-900` bg (default) or `teal-600` bg (accent variant)
- **Header text**: White, `body-sm`, semibold, tracked
- **Row borders**: `border-white/5`
- **Cell text**: `navy-200`, `body-sm`
- **Row hover**: `bg-white/[0.02]`
- **Border radius**: `rounded-panel` on container with `overflow-hidden`

### 3.7 CTA Buttons

| Variant     | Background         | Text         | Border          | Hover Effect              |
| ----------- | ------------------ | ------------ | --------------- | ------------------------- |
| Primary     | Teal gradient      | `navy-950`   | None            | Glow + scale 1.02         |
| Secondary   | Transparent        | White        | `white/20`      | `bg-white/5` + border/30  |
| Ghost       | Transparent        | `teal-400`   | None            | `bg-teal-400/10`          |
| Icon        | `surface`          | `navy-300`   | None            | Lighter surface + white   |

All buttons: `rounded-card` (12px), `font-heading`, `font-semibold`, transition 300ms.

### 3.8 Category Pills (Adhesive Types)

Row of teal pills matching the pitch deck "Our Solution" slide:

```
[Acrylic/PSA] [Cyanoacrylate] [Epoxy] [Hot-melt] [Polyurethane] [Rubber-based] [Silicone]
```

- **Background**: `teal-500`
- **Text**: White, `body-sm`, medium
- **Padding**: `px-5 py-2.5`
- **Border radius**: `rounded-card`
- **Hover**: Scale 1.05 + shift to `teal-400`

### 3.9 CTA Banner Section

Full-width section with centered content for "Request Demo" or "Get Started".

- **Background**: Subtle teal radial glow at 5% opacity
- **Title**: `display-md`, white, bold, centered
- **Subtitle**: `body-lg`, `navy-300`, max-width constrained
- **Button**: Centered `btn-primary`

### 3.10 Footer

- **Background**: `navy-950`, `border-top border-white/5`
- **Padding**: `py-16`
- **Layout**: 4-column grid (brand, product, company, legal) collapsing to stacked
- **Link color**: `navy-400` → `teal-400` on hover
- **Brand text**: `navy-400`, `body-sm`

---

## 4. Layout Specifications

### Page Structure

```
[Navigation]                    ← Fixed, 64px, blurred glass
[Hero]                          ← Full viewport height
[Problem Section]               ← alt background
[Solution / Features]           ← 3-col feature cards
[Technology / Performance]      ← Stats row + data table
[Market Opportunity]            ← Stats + chart
[Pricing]                       ← Data table (teal headers)
[Team]                          ← 4-col team cards
[CTA Banner]                    ← Full-width teal glow
[Footer]                        ← 4-col links + brand
```

### Container Widths

| Context        | Max Width | Token                 |
| -------------- | --------- | --------------------- |
| Narrow text    | 42rem     | `max-w-content-narrow`|
| Default        | 64rem     | `max-w-content-default`|
| Wide layout    | 80rem     | `max-w-content-wide`  |
| Full bleed     | 90rem     | `max-w-content-full`  |

### Section Spacing

| Screen     | Vertical Padding |
| ---------- | ---------------- |
| Mobile     | 64px (`py-16`)   |
| Desktop    | 128px (`py-32`)  |

### Responsive Breakpoints

Standard Tailwind breakpoints:
- `sm`: 640px
- `md`: 768px (nav links appear, 2-col grids)
- `lg`: 1024px (3-4 col grids, full layouts)
- `xl`: 1280px (max container widths kick in)

---

## 5. Brand Assets & Imagery Guidelines

### Logo Placement

- **Mark**: Teal gradient rounded square with "K" lettermark
- **Wordmark**: "K-Dense" in white, `heading-sm` weight
- **Minimum clear space**: 1x the height of the mark on all sides
- **On dark backgrounds**: White wordmark + teal mark
- **Minimum size**: 32px mark height

### Imagery Style

- **Scientific visualization**: Spectral plots, molecular structures, data charts
- **Color treatment**: Teal highlights on dark navy backgrounds
- **Photography**: (if used) Dark, high-contrast lab environments with teal accent lighting
- **Illustrations**: Abstract geometric patterns suggesting molecular bonds, spectral waves
- **Charts/graphs**: Teal for primary data series, navy-400 for secondary, white for labels

### Iconography

- **Style**: Outline icons, 24px default, 1.5px stroke
- **Color**: `teal-400` on dark, `navy-700` on light
- **Recommended**: Lucide React or Heroicons (outline set)

### Background Patterns

- **Grid**: Subtle 64px grid lines at 2% white opacity (`bg-grid` utility)
- **Dots**: Teal dot matrix at 7% opacity (`bg-dots` utility)
- **Use**: Hero section and CTA sections for visual texture

---

## 6. Animation & Motion

| Animation       | Duration | Easing     | Usage                    |
| --------------- | -------- | ---------- | ------------------------ |
| `fade-in`       | 600ms    | ease-out   | Section entry            |
| `fade-in-up`    | 600ms    | ease-out   | Card staggered entry     |
| `slide-in-left` | 600ms    | ease-out   | Left-aligned content     |
| `slide-in-right`| 600ms    | ease-out   | Right-aligned content    |
| `pulse-glow`    | 2000ms   | ease-in-out| CTA button idle state    |
| Hover scale     | 300ms    | ease-out   | Cards, buttons: 1.02x   |
| Color transition| 200ms    | linear     | Links, nav items         |

### Scroll-triggered animations

Use Intersection Observer to trigger `fade-in-up` on sections as they enter the viewport. Stagger card animations by 100ms per card.

---

## 7. Implementation Notes

### File Structure

```
design-system/
├── tailwind.config.ts      ← Tailwind theme extension
├── globals.css             ← Component classes + base styles
└── DESIGN-SYSTEM.md        ← This document
```

### Usage

1. Copy `tailwind.config.ts` theme values into your project's Tailwind config
2. Import `globals.css` in your app entry point
3. Use the component classes directly or as reference for React/Vue components
4. All component classes use Tailwind's `@apply` for consistency

### Font Loading

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Color Reference (Quick Copy)

```
Navy 950:  #171f2e
Navy 900:  #1e293b
Navy 800:  #243b53
Teal 400:  #2dd4bf
Teal 500:  #14b8a6
Teal 600:  #0d9488
White:     #ffffff
```
