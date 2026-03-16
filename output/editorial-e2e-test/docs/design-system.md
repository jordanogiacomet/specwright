# Design System

## Philosophy

- Favor clarity and content-first layout.
- Use consistent spacing scale and typography hierarchy.
- Minimize cognitive load across the application experience.

## Tokens

### Spacing

- **xs**: `4px`
- **sm**: `8px`
- **md**: `16px`
- **lg**: `24px`
- **xl**: `32px`
- **2xl**: `48px`

### Border Radius

- **sm**: `4px`
- **md**: `6px`
- **lg**: `12px`
- **full**: `9999px`

### Font

- **primary**: `Inter`
- **secondary**: `system-ui`
- **mono**: `JetBrains Mono, monospace`

### Font Size

- **xs**: `12px`
- **sm**: `14px`
- **base**: `16px`
- **lg**: `18px`
- **xl**: `20px`
- **2xl**: `24px`
- **3xl**: `30px`

### Line Height

- **tight**: `1.25`
- **normal**: `1.5`
- **relaxed**: `1.75`

### Shadow

- **sm**: `0 1px 2px rgba(0,0,0,0.05)`
- **md**: `0 4px 6px rgba(0,0,0,0.07)`
- **lg**: `0 10px 15px rgba(0,0,0,0.1)`

### Transition

- **fast**: `150ms ease`
- **normal**: `200ms ease`
- **slow**: `300ms ease`

### Colors

- **primary**: `blue-600`
- **primary_hover**: `blue-700`
- **background**: `white`
- **surface**: `white`
- **text**: `gray-900`
- **text_secondary**: `gray-600`
- **muted**: `gray-500`
- **border**: `gray-200`
- **destructive**: `red-600`
- **success**: `green-600`
- **warning**: `amber-500`
- **info**: `blue-500`
- **focus_ring**: `blue-500/50`

> Use Tailwind utility classes directly. Only use custom CSS for complex animations or layouts not expressible with utilities.

## Components

### Button
Primary action trigger
- Variants: primary, secondary, destructive, ghost

### Input
Text input field
- Variants: default, error, disabled

### Textarea
Multi-line text input

### Select
Dropdown selection

### Modal
Overlay dialog
- Variants: sm, md, lg

### Toast
Transient notification
- Variants: success, error, warning, info

### Dropdown
Action menu

### NavigationBar
Primary navigation bar

### ContentCard
Card for displaying content items in lists

### HeroBlock
Full-width hero section for landing pages

### Footer
Site-wide footer with links and metadata

## UX Patterns

- Provide clear status indicators for important workflow states.
- Use progressive disclosure for advanced options.

## Recommendations

- Use Tailwind CSS for styling — map tokens to Tailwind config or utility classes directly.
- Maintain a shared component library in src/components/ui/.
- Document component usage with prop types and examples.
- Follow WAI-ARIA patterns for interactive components (modals, dropdowns, tabs).
