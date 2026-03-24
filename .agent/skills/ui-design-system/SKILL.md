---

name: ui-design-system

description: Use this skill whenever creating or styling web interfaces. It defines the visual standard of the project with a modern design, consistent spacing, harmonious colors, micro-animations, and responsiveness.

---



\# Professional UI Design System



\## Objective

Ensure all generated interfaces have a clean, modern, and professional appearance, avoiding artificial or generic AI-like design patterns.



\## Core Guidelines

When working on web interfaces, ALWAYS follow these principles to build a highly professional, structured, and corporate-grade user experience.



---



\## 1. Visual Style \& Depth

\- Use a \*\*minimalist and professional\*\* design approach

\- Avoid exaggerated or flashy styles



\### Rules:

\- Avoid:

&nbsp; - Excessive rounded corners

&nbsp; - Heavy or artificial shadows

&nbsp; - Flashy gradients

\- Use:

&nbsp; - Subtle rounding only (`rounded-md` or `rounded-lg`)

&nbsp; - Soft, neutral shadows (`shadow-sm` or `shadow-md`)

&nbsp; - Clean, flat surfaces when possible



---



\## 2. Layout \& Structure

\- Remove sidebars in standard websites (use only when explicitly building dashboards)

\- Use \*\*top horizontal navigation\*\*

\- Follow this structure:

&nbsp; - Fixed header at the top

&nbsp; - Centered main content

&nbsp; - Simple footer



\### Layout System:

\- Use structured CSS grids (`grid`, `grid-cols-12`, `gap-6`)

\- Maintain strong alignment and spacing consistency

\- Use generous but controlled spacing (`p-6`, `p-8`, `gap-4`, `gap-6`)



---



\## 3. Navigation (Header)

\- Navigation must be at the top

\- Menu items aligned horizontally

\- Logo positioned on the \*\*right side\*\*

\- Keep navigation simple and objective



---



\## 4. Color Palette \& Backgrounds

\- Use \*\*sober and professional colors\*\*

&nbsp; - Prefer: gray, zinc, slate, white, black, muted blue

\- Avoid:

&nbsp; - Neon colors

&nbsp; - Overly vibrant palettes

&nbsp; - Strong gradients



\### Background Rules:

\- Do not use pure white for full pages

\- Use subtle neutral backgrounds (`bg-neutral-50`, `bg-zinc-50`)

\- Cards can use `bg-white`

\- Dark mode: use deep neutral grays (`bg-neutral-900`), not pure black



---



\## 5. Typography

\- Maintain a clear hierarchy:

&nbsp; - `h1`: `text-3xl` or `text-4xl`, `font-bold`, `tracking-tight`

&nbsp; - `h2/h3`: `text-xl` or `text-2xl`, `font-semibold`

&nbsp; - Body: `text-base` or `text-sm`, `text-gray-600`

\- Use modern sans-serif fonts (Inter, Roboto, system fonts)

\- Ensure readability with `leading-relaxed`



---



\## 6. Components

\### Buttons

\- Clean and discreet

\- No exaggerated effects

\- Subtle hover feedback only



\### Inputs

\- Simple design

\- Subtle borders (`border-neutral-300`)

\- No heavy styling



\### Cards

\- Minimal design

\- Avoid “inflated” look

\- Use:

&nbsp; - `bg-white`

&nbsp; - `border border-neutral-200`

&nbsp; - `shadow-sm`



---



\## 7. Interaction \& Micro-animations

\- All interactive elements must have transitions:

&nbsp; - `transition-all duration-300 ease-in-out`



\### Hover Behavior:

\- Buttons:

&nbsp; - Slight color change

&nbsp; - Minimal lift (`hover:-translate-y-0.5`)

\- Cards:

&nbsp; - Very subtle elevation (`hover:shadow-md`)



\### Focus:

\- Always include accessible focus states:

&nbsp; - `focus:ring-2 focus:ring-neutral-400 focus:outline-none`



---



\## 8. Responsiveness

\- Always build mobile-first

\- Use breakpoints (`sm`, `md`, `lg`, `xl`)

\- Mobile behavior:

&nbsp; - Navigation collapses into hamburger menu

&nbsp; - Content becomes single column



---



\## 9. Iconography

\- Use \*\*Lucide React\*\* for all icons

\- Keep icons:

&nbsp; - Clean

&nbsp; - Consistent

&nbsp; - Properly sized (`w-4 h-4` or `w-5 h-5`)



---



\## Behavior Rules

\- Always apply this system in every project

\- Never generate “AI-looking” interfaces

\- Avoid generic templates

\- Prioritize real-world corporate design patterns



---



\## Goal

Create interfaces indistinguishable from professionally designed products, focusing on clarity, structure, usability, and visual discipline.

