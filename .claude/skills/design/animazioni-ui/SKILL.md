---
name: emil-design-eng
description: UI polish, animation decisions, and micro-interaction design based on Emil Kowalski's philosophy. Use when implementing transitions, easing curves, component interactions, or any motion in the interface. Makes the UI feel alive instead of static.
version: 1.0.0
---

# Emil Design Engineering Skill

This skill encodes Emil Kowalski's philosophy on UI polish, component design, animation decisions, and the invisible details that make software feel great.

> "Good taste is not personal preference. It is a trained instinct." — Emil Kowalski

## Core Philosophy

**Unseen Details Compound**: Most UI refinements go unnoticed consciously, but their aggregate effect produces interfaces users love intuitively. The work is invisible; the result is not.

**Beauty as Differentiation**: In saturated markets, superior aesthetics and smooth interactions become genuine competitive advantages.

**Transitions over Keyframes**: For dynamic UI, prefer CSS transitions — they handle interruptions gracefully. Use keyframes only for non-interactive choreographed sequences.

---

## The Animation Decision Framework

Before animating anything, answer these questions in order:

### 1. Frequency Check
High-frequency actions (100+ per day) should NOT animate — ever.
- Keyboard shortcuts → instant
- Toggle switches → instant
- Tab switches → instant (or ≤100ms max)

### 2. Purpose Validation
Every animation needs a clear reason. Valid reasons:
- Spatial consistency (something moving to where it came from)
- State indication (something changing its status)
- Feedback (confirming a user action)
- Preventing jarring cuts (bridging visual gaps)

"Looks cool" is NOT a valid reason.

### 3. Easing Selection
| Situation | Curve |
|---|---|
| Element entering the screen | `ease-out` |
| Element leaving the screen | `ease-in` |
| Element moving on-screen | `ease-in-out` |
| Interactive / spring | Custom spring |

**Never use `ease-in` for UI entries** — it starts slow and feels sluggish.
**Always use custom curves** over browser defaults when possible.

### 4. Duration Limits
Keep UI animations under **300ms**. Specific targets:
- Button press feedback: 100–160ms
- Dropdowns / menus: 150–250ms
- Modals / sheets: 200–500ms
- Tooltips: 0ms delay on subsequent hovers (perceived speed)

---

## Technical Principles

### Transform & Opacity Only
Animate only properties that skip layout/paint and run on GPU:
- ✅ `transform` (translate, scale, rotate)
- ✅ `opacity`
- ❌ `width`, `height`, `margin`, `padding`, `top`, `left` (trigger layout)
- ❌ `background-color` alone (use carefully, no layout impact but paint cost)

### Never Scale from Zero
Nothing appears from complete absence in reality. Start from:
```css
/* ✅ */
opacity: 0;
transform: scale(0.95);

/* ❌ */
opacity: 0;
transform: scale(0);
```

### Popover Origin Awareness
Popovers must scale from their trigger point, not from center:
```css
/* Set dynamically based on trigger position */
transform-origin: var(--radix-popover-content-transform-origin);
```
Modals stay centered — they don't have a spatial origin.

### Spring Physics
Use spring animations for:
- Drag interactions
- Interruptible gestures (user can cancel mid-motion)
Springs maintain velocity when interrupted; CSS keyframes don't.

### Blur for Transitions
Subtle blur bridges visual gaps during crossfades, masking imperfect state transitions:
```css
filter: blur(4px);
opacity: 0;
```

---

## Component Patterns

### Button Press
Add instant physical feedback:
```css
button:active {
  transform: scale(0.97);
  transition: transform 100ms ease-out;
}
```

### Tooltips
Skip animation delay on subsequent hovers:
```css
/* First hover: 300ms delay before showing */
/* Subsequent hovers: 0ms delay */
```

### Drawers / Sheets
Use percentage-based translation for content-agnostic positioning:
```css
transform: translateY(100%); /* closed */
transform: translateY(0%);   /* open */
```
Never use pixel values — drawer height is dynamic.

### Clip-path Reveals
Powerful for reveals, overlays, comparison sliders:
```css
clip-path: inset(0 100% 0 0); /* hidden */
clip-path: inset(0 0% 0 0);   /* revealed */
transition: clip-path 300ms ease-out;
```
No extra DOM elements required.

---

## Building Loved Components

Principles from building Sonner (toast library):

1. **Minimize friction** — No complex setup, works out of the box
2. **Excellent defaults** matter more than options
3. **Cohesive motion** matching the component's personality
4. **Handle edge cases invisibly** — stacking, dismissal, overflow
5. **Use transitions over keyframes** for dynamic UI
6. **Build interactive documentation** — the demo IS the documentation

---

## Accessibility & Performance

### Reduced Motion
Respect the user's preference — don't eliminate animation, reduce it:
```css
@media (prefers-reduced-motion: reduce) {
  /* Gentler animations, not elimination */
  transition-duration: 0.01ms !important;
}
```

### Hover States
Gate hover-specific interactions behind pointer capability:
```css
@media (hover: hover) and (pointer: fine) {
  .button:hover { /* hover styles */ }
}
```
This prevents sticky hover states on touch devices.

### Performance
- CSS animations outperform JavaScript under heavy CPU load
- Test gestures on real devices — simulators lie
- Use `will-change: transform` sparingly (only when you KNOW an animation is coming)

---

## Anti-Patterns to Avoid

- `ease-in` on entering elements
- Animations on high-frequency interactions
- Scaling from `0` (use `0.95`)
- Pixel-based drawer translations
- Bounce/elastic easing on UI (dated, feels gamey)
- JavaScript animation when CSS suffices
- Animating layout properties (`width`, `height`, `margin`)
- Blocking interactions during animation (use `pointer-events: none` only during the animation itself)

---

## MisterLab Application Notes

When applying this skill to MisterLab:
- Use `--ml-*` CSS variables for timing where defined
- Respect the dark theme: animations on dark backgrounds need slightly higher opacity minimums (0.0 → 0.05 instead of 0.0)
- Match the "plasma" visual language: prefer sharp, precise motion over soft bouncy motion
- The app is used in field/panchina context: keep interactions fast and responsive (lean toward lower durations)
