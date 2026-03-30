# CSS & STYLING PATTERNS

> **Khi nào tải skill này:** CSS, Tailwind, Styling, Animation, Layout, Responsive

---

## TAILWIND RULES

**TW-001.** ALWAYS use utility-first approach:
```tsx
// GOOD - Tailwind utilities
<button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
  Submit
</button>

// BAD - Custom CSS for simple styles
<button className="submit-button">Submit</button>
```

**TW-002.** Extract components for repeated patterns:
```tsx
// components/ui/Button.tsx
const variants = {
  primary: 'bg-blue-600 hover:bg-blue-700 text-white',
  secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
  danger: 'bg-red-600 hover:bg-red-700 text-white',
} as const;

function Button({ variant = 'primary', children, ...props }: ButtonProps) {
  return (
    <button
      className={`px-4 py-2 rounded-lg transition-colors ${variants[variant]}`}
      {...props}
    >
      {children}
    </button>
  );
}
```

**TW-003.** Use design tokens via CSS variables:
```css
/* globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --color-primary: 59 130 246;    /* blue-500 */
    --color-background: 255 255 255;
    --radius: 0.5rem;
  }

  .dark {
    --color-primary: 96 165 250;    /* blue-400 */
    --color-background: 17 24 39;
  }
}
```

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: 'rgb(var(--color-primary) / <alpha-value>)',
        background: 'rgb(var(--color-background) / <alpha-value>)',
      },
    },
  },
};
```

---

## LAYOUT PATTERNS

**LAYOUT-001.** Use CSS Grid for 2D layouts:
```tsx
// Dashboard grid
<div className="grid grid-cols-12 gap-4">
  <aside className="col-span-2">Sidebar</aside>
  <main className="col-span-7">Content</main>
  <aside className="col-span-3">Widgets</aside>
</div>

// Auto-fit responsive grid
<div className="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-6">
  {cards.map(card => <Card key={card.id} {...card} />)}
</div>
```

**LAYOUT-002.** Use Flexbox for 1D alignment:
```tsx
// Center content
<div className="flex items-center justify-center min-h-screen">
  <Modal />
</div>

// Space between items
<header className="flex items-center justify-between px-4 py-3">
  <Logo />
  <Nav />
  <UserMenu />
</header>
```

---

## RESPONSIVE DESIGN

**RESP-001.** Mobile-first breakpoints:
```tsx
// Mobile first - add complexity at larger sizes
<div className="
  flex flex-col          /* Mobile: stack */
  md:flex-row            /* Tablet+: row */
  lg:gap-8               /* Desktop: more spacing */
">
  <div className="w-full md:w-1/3">Sidebar</div>
  <div className="w-full md:w-2/3">Main</div>
</div>
```

**RESP-002.** Container queries for component-level:
```css
/* Modern: Container queries */
.card-container {
  container-type: inline-size;
}

@container (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 1fr 2fr;
  }
}
```

---

## ANIMATION PATTERNS

**ANIM-001.** Use CSS transitions for simple states:
```tsx
<button className="
  transition-all duration-200 ease-out
  hover:scale-105 hover:shadow-lg
  active:scale-95
">
  Animated Button
</button>
```

**ANIM-002.** Use keyframes for complex animations:
```css
@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-slide-up {
  animation: slide-up 0.3s ease-out forwards;
}
```

**ANIM-003.** Respect reduced motion:
```tsx
<div className="
  motion-safe:animate-bounce
  motion-reduce:animate-none
">
  {/* Only animates if user hasn't set prefers-reduced-motion */}
</div>
```

---

## DARK MODE

**DARK-001.** Implement with CSS variables + class strategy:
```tsx
// Layout component
function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html className="dark"> {/* or controlled by state */}
      <body className="bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}

// Component usage
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  Content adapts to theme
</div>
```

---

## Z-INDEX SCALE

**Z-001.** Use consistent z-index scale:
```css
:root {
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-fixed: 300;
  --z-modal-backdrop: 400;
  --z-modal: 500;
  --z-popover: 600;
  --z-tooltip: 700;
}
```

```js
// tailwind.config.js
module.exports = {
  theme: {
    zIndex: {
      dropdown: '100',
      sticky: '200',
      fixed: '300',
      'modal-backdrop': '400',
      modal: '500',
      popover: '600',
      tooltip: '700',
    },
  },
};
```

---

## QUICK REFERENCE

| Pattern | Use Case |
|---------|----------|
| `flex` | 1D alignment, navigation |
| `grid` | 2D layouts, dashboards |
| `gap-*` | Spacing between items |
| `space-*` | Alternative to gap |
| `transition-*` | Hover/focus states |
| `animate-*` | Keyframe animations |
| `@container` | Component-responsive |
