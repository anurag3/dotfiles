# Backend / Software Engineering Traps

Domain-specific bullets to layer onto the core Pain Points / Architectural
checklist when the diff touches application/API/service code. ML-specific
traps live in `data-engineering.md` since ML code is usually data-pipeline
adjacent (training data, feature engineering).

## Pain Points

- **API contract traps** *(🟡 Major)*: request/response shape changed (renamed/removed field, changed type) with no versioning or deprecation path for existing consumers
- **Robustness violation** *(🟢 Minor; 🟡 Major if it breaks real clients)*: endpoint or parser is strict on accepted input (rejects unknown fields, exact-match shape) while being permissive on what it sends — minor upstream/downstream changes become needlessly breaking (Postel's Law / robustness principle)
- **Concurrency traps** *(🔴 Blocker if data-corrupting)*: shared mutable state accessed without a lock/guard, race condition between a read-then-write pair, non-idempotent retry on a non-idempotent endpoint
- **Resilience traps** *(🟡 Major)*: outbound call to another service/API with no timeout (can hang the caller indefinitely), no circuit breaker or backoff on a dependency known to be flaky
- **Error handling traps** *(🟡 Major)*: caught exception swallowed with no logging, error response leaking internal details (stack trace, SQL, file paths) to the client

## Architectural Issues

- **Testability** *(🟢 Minor–🟡 Major)*: business logic tightly coupled to a framework/IO boundary (DB client, HTTP client) with no seam for unit testing
- **N+1 / query traps** *(🟡 Major)*: loop issuing one query/call per item instead of a batched call, missing pagination on a list endpoint that can grow unbounded
- **Dependency scope** *(🟢 Minor)*: new dependency added for something the standard library or an existing dependency already covers

## OO Design Traps (SOLID)

For diffs with substantial class/trait hierarchies (common in Scala codebases). Dependency Inversion is covered by the base checklist's "tightly coupled" bullet — not repeated here.

- **Open/Closed violation** *(🟡 Major)*: adding a new case requires editing an existing class's internals (a `match`/`if-else` branching on type) instead of extending via a new subclass/trait — the abstraction doesn't support extension
- **Liskov substitution violation** *(🔴 Blocker if it breaks callers)*: an override narrows what the base type promises — throws where the base didn't, returns `null`/`None` where the base guaranteed a value, or weakens an invariant callers rely on
- **Interface segregation violation** *(🟢 Minor)*: a trait forces implementors to define methods they don't need (empty or `throw new UnsupportedOperationException` stubs) — a sign the trait should be split
- **Non-exhaustive sealed match** *(🟡 Major)*: a `match` over a `sealed trait`/`enum` uses a wildcard `case _ =>` instead of enumerating cases — a new case added later fails silently instead of a compile error
