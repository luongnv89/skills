# Language-Specific Checks

Per-language checklists for the Analysis phase. Read only the section matching
the detected language(s) of the target code — don't load the rest.

## JavaScript/TypeScript
- Array methods inside loops (map/filter/find in forEach)
- Missing async/await causing blocking
- Event listener leaks
- Unbounded arrays/objects

## Python
- List comprehensions vs generator expressions for large data
- Global interpreter lock considerations
- Context manager usage for resources
- N+1 query patterns

## Go
- Goroutine leaks (unbounded `go func()` without context cancellation)
- Unnecessary allocations in hot paths (use `sync.Pool`, pre-allocate slices)
- String concatenation in loops (use `strings.Builder`)
- Missing `defer` for resource cleanup

## Rust
- Unnecessary cloning (use references or `Cow<>` instead)
- Lock contention with `Mutex` when `RwLock` would suffice
- Unbounded `Vec` growth without `with_capacity`
- Blocking operations in async contexts

## Java
- Autoboxing in tight loops (use primitive types)
- String concatenation with `+` in loops (use `StringBuilder`)
- Synchronized blocks that are too broad
- Stream API misuse (unnecessary intermediate collections)

## General
- Premature optimization warnings (only flag if genuinely impactful)
- Database query patterns (N+1, missing indexes)
- I/O in hot paths
