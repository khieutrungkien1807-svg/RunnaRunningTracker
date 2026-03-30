# REACT PATTERNS & BEST PRACTICES

> **Khi nào tải skill này:** Component, Hook, State, Props, JSX, React

---

## COMPONENT RULES

**REACT-001.** ALWAYS dùng functional components với hooks:
```tsx
// GOOD
function UserCard({ user }: { user: User }) {
  const [isExpanded, setIsExpanded] = useState(false);
  return <div>...</div>;
}

// BAD - Class components (legacy)
class UserCard extends React.Component { }
```

**REACT-002.** NEVER mutate state trực tiếp:
```tsx
// GOOD
setItems(prev => [...prev, newItem]);
setUser(prev => ({ ...prev, name: 'New' }));

// BAD
items.push(newItem);
user.name = 'New';
```

**REACT-003.** ALWAYS dùng key unique cho lists (KHÔNG dùng index):
```tsx
// GOOD
{items.map(item => <Item key={item.id} {...item} />)}

// BAD
{items.map((item, index) => <Item key={index} {...item} />)}
```

---

## HOOKS RULES

**HOOK-001.** ALWAYS đặt hooks ở top level:
```tsx
function Component() {
  // GOOD - Top level
  const [state, setState] = useState(null);
  const data = useMemo(() => compute(state), [state]);

  // BAD - Inside condition
  if (condition) {
    const [x, setX] = useState(0); // ERROR!
  }
}
```

**HOOK-002.** ALWAYS cleanup effects:
```tsx
useEffect(() => {
  const subscription = api.subscribe(handler);
  const timer = setInterval(tick, 1000);

  return () => {
    subscription.unsubscribe();
    clearInterval(timer);
  };
}, []);
```

**HOOK-003.** ALWAYS memoize expensive computations:
```tsx
// Heavy computation - use useMemo
const sortedItems = useMemo(() =>
  items.sort((a, b) => a.price - b.price),
  [items]
);

// Callback passed to children - use useCallback
const handleClick = useCallback((id: string) => {
  setSelected(id);
}, []);
```

---

## PERFORMANCE PATTERNS

**PERF-001.** Use React.memo for pure components:
```tsx
const ExpensiveList = React.memo(function ExpensiveList({
  items
}: { items: Item[] }) {
  return (
    <ul>
      {items.map(item => <li key={item.id}>{item.name}</li>)}
    </ul>
  );
});
```

**PERF-002.** Lazy load routes và heavy components:
```tsx
const Dashboard = lazy(() => import('./Dashboard'));
const Analytics = lazy(() => import('./Analytics'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </Suspense>
  );
}
```

**PERF-003.** Virtualize long lists:
```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  return (
    <div ref={parentRef} style={{ height: 400, overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map(virtualRow => (
          <div
            key={virtualRow.key}
            style={{
              position: 'absolute',
              top: virtualRow.start,
              height: virtualRow.size,
            }}
          >
            {items[virtualRow.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## STATE MANAGEMENT

**STATE-001.** Prefer local state, lift only when needed:
```tsx
// Form state stays local
function ContactForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  // ...
}

// Shared state lifts to common ancestor or context
```

**STATE-002.** Use Context for global state (with caution):
```tsx
// Create typed context
const AuthContext = createContext<AuthContextType | null>(null);

function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be within AuthProvider');
  return context;
}

// Provider with memoized value
function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const value = useMemo(() => ({
    user,
    login: async (creds: Credentials) => { /* ... */ },
    logout: () => setUser(null),
  }), [user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
```

---

## ERROR BOUNDARIES

**ERROR-001.** ALWAYS wrap routes with error boundaries:
```tsx
class ErrorBoundary extends Component<Props, State> {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    logErrorToService(error, info);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

---

## ACCESSIBILITY (A11Y)

**A11Y-001.** ALWAYS include proper ARIA và semantic HTML:
```tsx
// GOOD
<button onClick={toggle} aria-expanded={isOpen} aria-controls="menu">
  Menu
</button>
<nav id="menu" hidden={!isOpen}>...</nav>

// BAD
<div onClick={toggle}>Menu</div>
```

**A11Y-002.** ALWAYS handle keyboard navigation:
```tsx
function MenuItem({ onSelect }: { onSelect: () => void }) {
  return (
    <li
      role="menuitem"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect();
        }
      }}
    >
      Item
    </li>
  );
}
```

---

## QUICK REFERENCE

| Pattern | When to Use |
|---------|-------------|
| `useState` | Simple local state |
| `useReducer` | Complex state logic |
| `useContext` | Shared state across tree |
| `useMemo` | Expensive calculations |
| `useCallback` | Stable function references |
| `useRef` | DOM refs, mutable values |
| `useEffect` | Side effects, subscriptions |
| `React.memo` | Prevent re-renders |
| `lazy/Suspense` | Code splitting |
