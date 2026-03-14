# Design System

## Philosophy

- Favor workflow clarity and fast task-oriented navigation.
- Optimize for dense, readable operational interfaces.
- Reduce cognitive load for recurring internal workflows.

## Tokens

- spacing_scale: 4px base grid
- border_radius: 6px default
- font_primary: Inter
- font_secondary: System UI

## Components

- AppShell
- SidebarNav
- TopBar
- Button
- Input
- Textarea
- Select
- Modal
- Toast
- Dropdown
- DataTable
- FilterBar
- StatusBadge
- WorkItemCard
- DetailDrawer
- DatePicker
- AssigneeSelect
- NavigationBar
- HeroBlock
- Footer

## UX Patterns

- Use clear status states and visible progress markers.
- Keep common actions close to work-item context.
- Use optimistic UI carefully for low-risk edits.
- Support keyboard-friendly workflows where practical.
- Design text containers to handle locale expansion gracefully.
- Ensure locale switching is easy to find and clearly reflected in the UI.

## Recommendations

- Use Tailwind CSS or CSS variables for the token system.
- Maintain a shared component library where possible.
- Document component usage and accessibility expectations.