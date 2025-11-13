# API File Relevance Audit

## Summary Table
| Module | Classification |
| --- | --- |
| `crapssim_api/determinism.py` | Passive / Legacy-ish |
| `crapssim_api/hand_state.py` | Required |
| `crapssim_api/rng.py` | Passive / Legacy-ish |
| `crapssim_api/session_store.py` | Required |
| `crapssim_api/state.py` | Passive / Legacy-ish |
| `crapssim_api/version.py` | Required |

## Module Reports
### determinism.py
- inbound imports: _none_
- outbound imports: `json`, `hashlib`, `dataclasses.dataclass`, `typing.Any`, `typing.Iterable`, `typing.Literal`, `.rng.SeededRNG`
- tests referencing: _none_
- runtime reachability: not imported by HTTP, session management, tape, or capabilities stacks; only referenced inside the determinism module itself
- relevance classification: Passive / Legacy-ish
- justification: Provides a determinism harness intended to record RNG activity, but no other module or test imports it. It pairs with the unused `SeededRNG` helper and is not wired into the current V2 request paths, suggesting it is a placeholder for future determinism tooling rather than active API flow.

### hand_state.py
- inbound imports: `crapssim_api.session_store`
- outbound imports: `dataclasses.dataclass`, `typing.Any`, `typing.Dict`, `typing.List`, `typing.Literal`, `typing.Optional`, `typing.Tuple`
- tests referencing: _none_
- runtime reachability: accessed by `session_store` which feeds `http.start_session` and `http.step_roll`, driving HTTP responses and event synthesis; no direct links to `session.py`, tape tooling, or capability modules
- relevance classification: Required
- justification: `HandState` encapsulates puck/point tracking and emits hand transition events that `http.step_roll` transforms into API events. Removing it would break step roll snapshots and event output consumed by existing HTTP clients.

### rng.py
- inbound imports: `crapssim_api.determinism`
- outbound imports: `random`, `typing.Iterable`, `typing.TypeVar`, `typing.Any`
- tests referencing: _none_
- runtime reachability: only reachable through `determinism.py`; not imported by HTTP, session, tape, or capabilities layers
- relevance classification: Passive / Legacy-ish
- justification: Implements the RNG wrapper that the determinism harness expects, but the harness is not referenced anywhere. Until determinism tooling is integrated, this helper is effectively dormant alongside `determinism.py`.

### session_store.py
- inbound imports: `crapssim_api.http`
- outbound imports: `typing.Any`, `typing.Dict`, `.hand_state.HandState`
- tests referencing: `tests/api/test_p5c0_scaffold.py` exercises session isolation indirectly through the HTTP `/step_roll` endpoint
- runtime reachability: core to HTTP lifecycle—`http.start_session`, `http.apply_action`, and `http.step_roll` use `SESSION_STORE` to maintain per-session hand data; no dependencies on `session.py`, tape, or capability helper modules beyond what HTTP already pulls in
- relevance classification: Required
- justification: Powers the request-scoped state for every HTTP interaction. Existing API tests depend on its behavior to isolate sessions and to populate responses with hand metadata.

### state.py
- inbound imports: _none_
- outbound imports: `.version.ENGINE_API_VERSION`, `.version.CAPABILITIES_SCHEMA_VERSION`
- tests referencing: _none_
- runtime reachability: not imported by HTTP, session, tape, or capability-related modules
- relevance classification: Passive / Legacy-ish
- justification: Provides a stubbed `snapshot_from_table` helper meant for a future expansion. With no inbound imports or tests, it currently serves as a placeholder rather than part of the active API flow.

### version.py
- inbound imports: `crapssim_api.http`, `crapssim_api.state`, `crapssim_api.__init__`, `tests/api/test_baseline_smoke.py`
- outbound imports: _none_
- tests referencing: `tests/api/test_baseline_smoke.py` checks exposed engine API tags
- runtime reachability: feeds HTTP responses (`start_session`, `apply_action`, `step_roll`) with version metadata and supports identity helpers exposed through the package init; not used by `session.py` or tape utilities
- relevance classification: Required
- justification: Provides canonical API versioning constants and helpers consumed by HTTP endpoints and package exports. Tests assert its values, making it integral to the public API contract.

## Recommendations
- Keep `hand_state.py`, `session_store.py`, and `version.py` under active maintenance—they directly support HTTP responses and have test coverage.
- Consider documenting future integration plans for `determinism.py`/`rng.py` or migrating them to a dedicated determinism toolkit module to clarify their dormant status.
- Decide whether to expand or retire `state.py` once the V2 snapshot schema is finalized; it currently carries only placeholder data.
