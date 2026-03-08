# SimulaQron Development Conventions

## Hard Requirements

### Examples
- Examples MUST always use separate files per node (e.g. `nodeTest-client.py`, `nodeTest-server.py`), never single-file programs. Students must be able to run each node on a separate machine.
- Follow the `new-sdk/template-client-server` structure: two node scripts + `run.sh` + `terminate.sh` + config JSONs.
- All nodes should print their own output (not rely on return values visible only to the test harness).

### Connection Pattern
- Prefer creating a `NetQASMConnection` once and reusing it with `flush()` for multi-round quantum programs, rather than opening/closing with `with` each round.
- `conn.flush()` is the sync point that makes measurement results readable via `int(m)`.

### Backends
- Use `stabilizer` backend by default in examples and tests unless non-Clifford gates are needed.
- `projectq` is deprecated / hard to install. Prefer `qutip` when full state simulation is needed.

## File Conventions
- **Examples:** `examples/new-sdk/` — all new examples use the new SDK
- **Tests:** `tests/slow/sdk/` — SDK-level integration tests
- **Core code:** `simulaqron/` — simulator source
- **Docs:** `docs/` — Sphinx documentation (currently outdated, being rewritten)

## Virtual Environment
- The project venv is at `.venv/` — activate with `source .venv/bin/activate`
- Install with `pip install -e .` (skip `[test]` if projectq build fails)
