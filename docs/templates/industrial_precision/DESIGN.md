---
name: Industrial Precision
colors:
  surface: '#f9f9fe'
  surface-dim: '#dad9de'
  surface-bright: '#f9f9fe'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f3f8'
  surface-container: '#eeedf2'
  surface-container-high: '#e8e8ed'
  surface-container-highest: '#e2e2e7'
  on-surface: '#1a1c1f'
  on-surface-variant: '#43474f'
  inverse-surface: '#2f3034'
  inverse-on-surface: '#f1f0f5'
  outline: '#737780'
  outline-variant: '#c3c6d1'
  surface-tint: '#3a5f94'
  primary: '#001e40'
  on-primary: '#ffffff'
  primary-container: '#003366'
  on-primary-container: '#799dd6'
  inverse-primary: '#a7c8ff'
  secondary: '#545f72'
  on-secondary: '#ffffff'
  secondary-container: '#d5e0f7'
  on-secondary-container: '#586377'
  tertiary: '#381300'
  on-tertiary: '#ffffff'
  tertiary-container: '#592300'
  on-tertiary-container: '#d8885c'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a7c8ff'
  on-primary-fixed: '#001b3c'
  on-primary-fixed-variant: '#1f477b'
  secondary-fixed: '#d8e3fa'
  secondary-fixed-dim: '#bcc7dd'
  on-secondary-fixed: '#111c2c'
  on-secondary-fixed-variant: '#3c475a'
  tertiary-fixed: '#ffdbca'
  tertiary-fixed-dim: '#ffb690'
  on-tertiary-fixed: '#341100'
  on-tertiary-fixed-variant: '#723610'
  background: '#f9f9fe'
  on-background: '#1a1c1f'
  surface-variant: '#e2e2e7'
typography:
  h1:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  section-title:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-base:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-bold:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  data-tabular:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 16px
  margin-page: 24px
  padding-card: 20px
  stack-sm: 8px
  stack-md: 16px
---

## Brand & Style

The design system is engineered for high-stakes industrial environments where precision, speed of cognition, and data integrity are paramount. The brand personality is rooted in reliability and functional utility, reflecting the heavy-duty nature of industrial workflows while maintaining a modern, sophisticated corporate interface.

The visual style follows a **Corporate / Modern** approach with a strong lean toward **Minimalism**. By prioritizing whitespace around critical data points and using a high-contrast palette, the system minimizes cognitive load for operators and managers. Every element serves a functional purpose, eschewing decorative flourishes for a "utility-first" aesthetic that ensures readability under various lighting conditions common in industrial settings.

## Colors

The palette is anchored by a **Deep Industrial Blue**, derived from the core brand identity, representing stability and expertise. This is supported by a range of neutral grays that define the architectural boundaries of the application.

- **Primary Canvas:** Content areas are strictly white (`#FFFFFF`) to provide the highest possible contrast for data entry and reading.
- **Structural Grays:** A cool-toned gray (`#F8F9FA`) is used for the application backdrop to reduce eye strain, while mid-tones are reserved for borders and inactive states.
- **Semantic Feedback:** Status colors (Green, Yellow, Red) are applied with high saturation to ensure they are immediately distinguishable. They are used for conditional formatting in tables and critical status indicators, never as primary decorative elements.

## Typography

This design system utilizes **Inter** for its exceptional legibility in digital interfaces and its neutral, systematic character. 

The type hierarchy is optimized for information-dense screens:
- **Section Titles (18px):** Used for primary module headers and major card titles to establish clear landmarks.
- **Body Text (14px):** The standard size for all descriptive text and form labels, providing a balance between density and readability.
- **Data Sets:** Tabular data uses a slightly reduced size (13px) to maximize the number of rows visible on a single screen without sacrificing clarity.
- **High Contrast:** All primary text is set in near-black for maximum contrast against white backgrounds.

## Layout & Spacing

The layout philosophy is built on a **Fluid Grid** system that adapts to the wide-screen monitors typically found in control rooms and corporate offices. 

- **Grid System:** A 12-column grid with a fixed 16px gutter. 
- **Density:** The system uses a 4px base unit to allow for a compact "Industrial Density" setting where padding is minimized to show more data, and a "Standard" setting for management dashboards.
- **Alignment:** All elements must align to the grid. Form fields should span consistent column widths (e.g., 3, 4, or 6 columns) to maintain a disciplined, professional structure.

## Elevation & Depth

To maintain a minimalist and functional look, this design system avoids heavy shadows. Depth is communicated through **Tonal Layers** and **Low-Contrast Outlines**.

- **Surface Tiers:** The main application background is at the lowest level. Content cards and data tables are "raised" visually using a pure white background and a subtle 1px border (`#DEE2E6`).
- **Interactive States:** Hovering over interactive elements (like table rows or buttons) triggers a subtle background color shift rather than a shadow change.
- **Modals:** Only global modals use an ambient, low-opacity shadow to provide focus, ensuring they sit clearly above the primary workspace.

## Shapes

The design system uses **Soft (4px)** roundedness. This subtle rounding provides a modern touch while maintaining the structured, rigid feel of industrial software. 

- **Components:** Buttons, input fields, and cards all share the same 4px radius. 
- **Tags/Status Chips:** These may use a slightly larger radius (rounded-lg) for visual differentiation from interactive inputs, but should never be full-pill shaped to ensure they don't appear overly casual.

## Components

### Buttons
- **Primary:** Solid Deep Blue background with White text. Used for the main "action" on a page (e.g., Save, Submit, Start Process).
- **Secondary:** Outline style with a 1px Blue border and Blue text. Used for supporting actions.
- **Tertiary/Ghost:** No background or border. Used for low-priority actions like "Cancel" or "Reset."

### Form Elements
- **Inputs:** 1px border (`#CED4DA`), 40px height for standard touch/click targets. Labels are positioned above the field in SemiBold 12px.
- **States:** Active inputs receive a 1px Primary Blue border and a subtle light blue glow. Error states use the Status Red (`#dc3545`) for borders and validation text.

### AgGrid Table Styling
As a data-heavy industrial tool, the table is the most critical component:
- **Header:** Light gray background (`#F1F3F5`), SemiBold text, 1px bottom border.
- **Rows:** 36px height for high density. Alternate row striping (Zebra) is used to help eye tracking across long rows.
- **Cell Content:** Left-aligned for text, right-aligned for numerical values. 
- **Status Cells:** Use a colored "pill" or left-hand border accent using the defined status colors to indicate line health or process stages.

### Cards
- Standard containers for grouping related information. Features a 1px border, no shadow, and a 20px internal padding.