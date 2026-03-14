# Design System

## Philosophy

- Favor clarity and content-first layout.
- Use consistent spacing scale and typography hierarchy.
- Minimize cognitive load for editorial workflows.

## Tokens

- spacing_scale: 4px base grid
- border_radius: 6px default
- font_primary: Inter
- font_secondary: System UI

## Components

- Button
- Input
- Textarea
- Select
- Modal
- Toast
- Dropdown
- RichTextEditor
- MediaPicker
- ContentList
- ContentStatusBadge
- PublishControls
- NavigationBar
- HeroBlock
- ContentCard
- Footer

## UX Patterns

- Use optimistic UI for publishing actions
- Provide clear status indicators for draft vs published content
- Autosave editorial content where possible
- Preview mode should match public rendering exactly.

## Recommendations

- Use Tailwind CSS or CSS variables for token system.
- Maintain a component library shared between admin and public site.
- Document component usage and accessibility constraints.