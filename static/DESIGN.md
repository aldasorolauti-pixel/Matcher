---
name: Monochrome Slate Bento
colors:
  surface: '#121316'
  surface-dim: '#121316'
  surface-bright: '#38393c'
  surface-container-lowest: '#0d0e11'
  surface-container-low: '#1b1b1f'
  surface-container: '#1f1f23'
  surface-container-high: '#292a2d'
  surface-container-highest: '#343538'
  on-surface: '#e3e2e6'
  on-surface-variant: '#c4c7c9'
  inverse-surface: '#e3e2e6'
  inverse-on-surface: '#2f3034'
  outline: '#8e9193'
  outline-variant: '#444749'
  surface-tint: '#c4c7c9'
  primary: '#ffffff'
  on-primary: '#2d3133'
  primary-container: '#e0e3e5'
  on-primary-container: '#626567'
  inverse-primary: '#5c5f61'
  secondary: '#c1c7d3'
  on-secondary: '#2b313b'
  secondary-container: '#434954'
  on-secondary-container: '#b3b9c5'
  tertiary: '#ffffff'
  on-tertiary: '#2c303a'
  tertiary-container: '#dfe2ee'
  on-tertiary-container: '#60646f'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e0e3e5'
  primary-fixed-dim: '#c4c7c9'
  on-primary-fixed: '#191c1e'
  on-primary-fixed-variant: '#444749'
  secondary-fixed: '#dde3f0'
  secondary-fixed-dim: '#c1c7d3'
  on-secondary-fixed: '#161c25'
  on-secondary-fixed-variant: '#414751'
  tertiary-fixed: '#dfe2ee'
  tertiary-fixed-dim: '#c3c6d2'
  on-tertiary-fixed: '#171c24'
  on-tertiary-fixed-variant: '#434751'
  background: '#121316'
  on-background: '#e3e2e6'
  surface-variant: '#343538'
typography:
  headline-xl:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Geist
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  body-sm:
    fontFamily: Geist
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 0.75rem
  margin: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 2rem
---

## Brand & Style

This design system embodies an ultra-minimalist, precision-engineered desktop wireframe aesthetic inspired by modern macOS ergonomics and modular bento-box layouts. It is tailored for creative directors, system architects, and productivity power users who value zero cognitive friction, tactile structural clarity, and disciplined negative space.

The emotional tone is calm, analytical, and meticulously organized. The style merges pure functional minimalism with subtle industrial desktop wireframe sensibilities:
- Flat, velvety matte neutral surfaces layered without ostentatious drop shadows.
- Disciplined hairline borders that distinguish hierarchical bounds without visual clutter.
- Generous, organic corner curves paired with rigid structural alignment.
- A strictly monochromatic slate palette where luminance—rather than hue—communicates state, depth, and priority.

## Colors

The palette adheres strictly to a graded grayscale spectrum spanning deep carbon blacks, neutral slate tones, and crisp architectural whites. Color is completely decoupled from hue, relying strictly on value contrast to denote hierarchy:

- **Canvas & Backdrops (`#121316`)**: Deep, low-reflectance charcoal that establishes quiet space behind floating containers.
- **Surface Layer 1 (`#1C1E22`)**: The foundational bento tile container fill, providing a solid matte floor.
- **Surface Layer 2 (`#272A30`)**: Elevated sub-cards, nested modules, and inactive toolbar pill controls.
- **Surface Layer 3 (`#383C45`)**: Hover targets, active selection zones, and secondary interactive items.
- **Border & Hairline Stroke (`#2E323A` / `#3E434D`)**: 1px structural outlines that define boundaries crisply against dark backgrounds.
- **Primary Content (`#F1F3F5`)**: High-contrast, near-white text and primary active icons.
- **Muted Content (`#9096A2`)**: Mid-tier metadata, secondary labels, and placeholder shapes.
- **Subtle Details (`#4A4E58`)**: Dividers, disabled state indicators, and dormant wireframe iconography.

## Typography

Typography delivers geometric precision, legibility, and technical authority. **Geist** serves as the primary typographic voice for all structural headers and prose, providing sharp geometric apertures, balanced numerals, and clean rendering on high-density displays.

**JetBrains Mono** is utilized for contextual meta-information, technical wireframe coordinates, system metrics, and badges. Its fixed-width cadence grounds the modular UI with an architectural, instrument-like feel.

Line heights are kept compact to align with dense information grids, while subtle negative tracking on large headlines preserves a cohesive, engineered appearance.

## Layout & Spacing

The structural foundation is a strict, cohesive bento grid composed of rounded modular panels separated by uniform gutters. Layout rules reflect native macOS multi-pane architecture:

- **Desktop Layout**: An asymmetric, modular multi-column composition. High-level groupings feature a persistent slim vertical control rail (left), a focal dominant viewport or workspace (center), and stacked secondary contextual panels or widget stacks (right and bottom).
- **Gutter Rhythm**: Gutters are anchored to `0.75rem` (12px), creating tight, surgical boundaries that lock containers into a single cohesive chassis.
- **Negative Space Strategy**: Bento tiles contain balanced internal padding (`space-lg`), insulating internal widgets while maintaining dense inter-module coherence.
- **Responsive Adaptation**:
  - *Large Desktop (>1440px)*: Multi-row, multi-column bento modules lock into fixed proportional relations inside an outer canvas envelope.
  - *Medium Screen / Tablet (768px - 1024px)*: The right-hand secondary stack reflows underneath the central focal viewport; sidebar rail condenses to icon-only.
  - *Compact / Mobile (<768px)*: Modules collapse vertically into single-column fluid cards with reduced outer margin (`1rem`) and unified `0.5rem` gutters.

## Elevation & Depth

Visual hierarchy rejects simulated directional light sources, diffuse drop shadows, and high-opacity specular gradients. Depth is established through **flat surface stacking** and **controlled edge definition**:

1. **Base Foundation**: The master frame background sits at `#121316`.
2. **Container Tier**: Primary bento modules sit flat at `#1C1E22`, encased in a unified 1px border (`#2E323A`).
3. **Internal Sub-Surfaces**: Nested cards, active toolbars, and grouped pills sit on `#272A30` with matching hairline perimeter rings (`#3E434D`).
4. **Interactive Highlights**: Focused states or active selections lift to `#383C45` with crisp `#525866` borders.
5. **No Diffusion**: Shadows are omitted entirely in favor of matte planar contrast, ensuring all UI elements remain crisp and non-blurry across varying display hardware.

## Shapes

The design language balances generous, friendly outer curves with tight, functional inner primitives:
- **Master Bento Modules & Main Panes**: Styled with a comfortable `rounded-xl` (1.5rem / 24px) radius, establishing distinct "enclosures" reminiscent of macOS window containers.
- **Nested Cards & Sub-Panels**: Configured with `rounded-lg` (1rem / 16px) to echo the curvature of parent containers harmoniously.
- **Interactive Primitives**: Buttons, segment switches, input bars, and pill indicators apply full continuous pill geometry (`rounded-full`) or standardized `rounded-md` (0.5rem / 8px).
- **Structural Notches & Floating Connectors**: Peripheral tabs and sub-docks smoothly integrate into adjacent panel contours, celebrating continuous organic geometry.

## Components

### Buttons & Pills
- **Primary Action Button**: High-contrast matte white background (`#F1F3F5`) with solid dark text (`#121316`). Full pill shape, zero shadow.
- **Secondary / Ghost Button**: Translucent slate container (`#272A30`) with hairline stroke (`#3E434D`) and neutral text (`#F1F3F5`). On hover, background transitions to `#383C45`.
- **Icon Action Buttons**: Pure geometric circular or pill containers with embedded wireframe iconography (`16x16px`), centered with strict optical alignment.

### Input Fields & Search Bars
- Elongated pill or `rounded-lg` geometry with low-reflectance surface `#1C1E22` and border `#2E323A`.
- Left-aligned accessory icons (search glass, command symbol) rendered in `#9096A2`.
- Focus state is communicated by a crisp 1px stroke shift to `#F1F3F5` without glowing outer rings.

### Bento Panels & Cards
- Outer shell framed in 1px stroke `#2E323A` over `#1C1E22`.
- Nested lists and stack layouts within cards feature subtle `#272A30` pill dividers or clean whitespace gutters.
- Visual wireframe placeholders utilize soft slate blocks (`#272A30`) with rounded corners to denote media, charts, or structural avatars.

### Chips & Badges
- Compact pill-shaped containers featuring `label-sm` typography (JetBrains Mono).
- Background `#272A30` with soft `#3E434D` outline. Content displayed in muted slate `#9096A2` or high-priority white `#F1F3F5`.

### Checkboxes, Switches & Radios
- **Checkboxes**: 16x16px rounded squares (4px radius) in `#272A30` bordered by `#3E434D`. Checked state fills with `#F1F3F5` featuring a dark checkmark.
- **Toggle Switches**: Compact pill track (`#272A30`) with a floating circular thumb (`#9096A2`). Active state fills the thumb with `#F1F3F5`.

### Navigation Dock & Toolbars
- Floating vertical or horizontal rails featuring clustered icon buttons.
- Inactive nodes sit in `#9096A2`; active nodes occupy an illuminated `#F1F3F5` pill with dark iconography.