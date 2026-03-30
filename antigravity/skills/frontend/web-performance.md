# WEB PERFORMANCE

> **Khi nào tải skill này:** Performance, Vitals, Optimization, Lazy Load, Bundle, LCP

---

## CORE WEB VITALS

**VITALS-001.** Key metrics:
```
LCP (Largest Contentful Paint) < 2.5s
  → Largest visible element loaded

FID (First Input Delay) < 100ms
  → Time until interactive

CLS (Cumulative Layout Shift) < 0.1
  → Visual stability

INP (Interaction to Next Paint) < 200ms
  → Responsiveness to interactions
```

---

## IMAGE OPTIMIZATION

**IMG-001.** Next.js Image component:
```tsx
import Image from 'next/image';

// Automatic optimization
<Image
  src="/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  priority  // LCP image
  placeholder="blur"
  blurDataURL={blurHash}
/>

// Responsive
<Image
  src="/product.jpg"
  alt="Product"
  fill
  sizes="(max-width: 768px) 100vw, 50vw"
  style={{ objectFit: 'cover' }}
/>
```

**IMG-002.** Manual optimization:
```html
<!-- Modern formats with fallback -->
<picture>
  <source srcset="image.avif" type="image/avif">
  <source srcset="image.webp" type="image/webp">
  <img src="image.jpg" alt="Description" loading="lazy">
</picture>

<!-- Responsive images -->
<img
  src="image-800.jpg"
  srcset="
    image-400.jpg 400w,
    image-800.jpg 800w,
    image-1200.jpg 1200w
  "
  sizes="(max-width: 600px) 100vw, 50vw"
  loading="lazy"
  decoding="async"
  alt="Description"
>
```

---

## CODE SPLITTING

**SPLIT-001.** Route-based splitting:
```tsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

**SPLIT-002.** Component-level splitting:
```tsx
const HeavyChart = lazy(() => import('./HeavyChart'));
const PDFViewer = lazy(() => import('./PDFViewer'));

function Dashboard() {
  const [showChart, setShowChart] = useState(false);

  return (
    <div>
      <button onClick={() => setShowChart(true)}>Show Chart</button>

      {showChart && (
        <Suspense fallback={<ChartSkeleton />}>
          <HeavyChart data={data} />
        </Suspense>
      )}
    </div>
  );
}
```

---

## BUNDLE OPTIMIZATION

**BUNDLE-001.** Analyze bundle:
```bash
# Next.js
ANALYZE=true npm run build

# Vite
npx vite-bundle-visualizer

# Webpack
npx webpack-bundle-analyzer stats.json
```

**BUNDLE-002.** Tree shaking:
```typescript
// BAD - imports entire library
import _ from 'lodash';
_.debounce(fn, 300);

// GOOD - import specific function
import debounce from 'lodash/debounce';
debounce(fn, 300);

// BEST - use native or smaller alternatives
const debounce = (fn: Function, ms: number) => {
  let timeout: NodeJS.Timeout;
  return (...args: any[]) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), ms);
  };
};
```

---

## CACHING STRATEGIES

**CACHE-001.** Static assets:
```typescript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/:all*(svg|jpg|png|webp|avif|woff2)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
};
```

**CACHE-002.** Service worker:
```typescript
// sw.ts
const CACHE_NAME = 'v1';
const STATIC_ASSETS = ['/offline.html', '/app.css', '/app.js'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('/offline.html'))
    );
  }
});
```

---

## RENDERING PATTERNS

**RENDER-001.** Choose right strategy:
```
SSG (Static Site Generation)
  → Marketing pages, blogs
  → Build-time rendering

SSR (Server-Side Rendering)
  → SEO + personalized content
  → Request-time rendering

ISR (Incremental Static Regeneration)
  → Frequently updated content
  → Background revalidation

CSR (Client-Side Rendering)
  → Dashboards, SPAs
  → Browser rendering
```

**RENDER-002.** Next.js App Router:
```tsx
// Static (default)
export default function Page() {
  return <div>Static content</div>;
}

// Dynamic
export const dynamic = 'force-dynamic';

// ISR
export const revalidate = 60; // Revalidate every 60s

// Stream with Suspense
export default async function Page() {
  return (
    <div>
      <h1>Page Title</h1>
      <Suspense fallback={<Skeleton />}>
        <SlowComponent />
      </Suspense>
    </div>
  );
}
```

---

## RESOURCE HINTS

**HINT-001.** Preload critical resources:
```html
<!-- Preload critical assets -->
<link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/hero.webp" as="image">

<!-- Prefetch next page -->
<link rel="prefetch" href="/dashboard">

<!-- Preconnect to APIs -->
<link rel="preconnect" href="https://api.example.com">
<link rel="dns-prefetch" href="https://analytics.example.com">
```

---

## QUICK REFERENCE

| Metric | Target | Impact |
|--------|--------|--------|
| LCP | < 2.5s | User perception |
| FID | < 100ms | Interactivity |
| CLS | < 0.1 | Visual stability |
| INP | < 200ms | Responsiveness |
| TTI | < 3.8s | Time to interactive |
| TBT | < 200ms | Main thread blocking |

| Technique | Benefit |
|-----------|---------|
| Code splitting | Smaller initial bundle |
| Lazy loading | Load on demand |
| Image optimization | Faster LCP |
| Caching | Repeat visits |
| Preloading | Critical resources |
| SSG/ISR | Faster TTFB |
