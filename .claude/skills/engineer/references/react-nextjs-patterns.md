# React & Next.js Patterns

## Compound Components
Share state between related components without prop drilling:
```tsx
const Tabs = ({ children, defaultTab = 0 }) => {
  const [active, setActive] = useState(defaultTab);
  return <TabsContext.Provider value={{ active, setActive }}>{children}</TabsContext.Provider>;
};
Tabs.List = TabList;
Tabs.Panel = TabPanel;
```

## Data Fetching (App Router)
```tsx
// Parallel — always prefer Promise.all over sequential awaits
const [user, posts] = await Promise.all([getUser(id), getPosts(id)]);

// Streaming — wrap slow data in Suspense
<Suspense fallback={<Skeleton />}>
  <SlowComponent />
</Suspense>

// Revalidation
fetch(url, { next: { revalidate: 60 } })  // ISR: revalidate every 60s
fetch(url, { cache: 'no-store' })          // Always fresh (SSR)
```

## State Management Decision
```
Local UI state (toggle, form) → useState
Cross-component state, few values → useContext
Global app state, frequent updates → Zustand
Server state / async data → TanStack Query
Form state → React Hook Form
```

## Performance Patterns
```tsx
// Memoization — only when profiler shows it helps
const ExpensiveList = memo(({ items }) => <ul>...</ul>);
const sorted = useMemo(() => items.sort(...), [items]);
const handleClick = useCallback(() => doThing(id), [id]);

// Dynamic import for heavy components
const HeavyChart = dynamic(() => import('./Chart'), { ssr: false });

// Virtualization for long lists
// Use @tanstack/react-virtual
```

## Common Gotchas
| Issue | Fix |
|-------|-----|
| Hydration mismatch | Check server vs client rendering differences |
| useEffect infinite loop | Review dependency array — missing dep or unstable ref |
| Stale closure | Use useRef for mutable values, or include in deps |
| Re-render on every parent render | React.memo + stable callbacks |
