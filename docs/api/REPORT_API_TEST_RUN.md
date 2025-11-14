# CrapsSim API — Test Sweep Report

_Date:_ 2025-11-14
_Branch:_ API
_Commit:_ `2ad8b18`

## Environment

- Python version: `Python 3.11.12`
- Platform: `linux`
- Installed API extras: `.[api]` (yes)
- Key packages:
  - numpy: `2.3.4`
  - fastapi: `0.121.2`
  - pydantic: `2.12.4`
  - uvicorn: `0.38.0`

If you created or modified any requirements/extras to satisfy tests, list them here:

```text
- Added fastapi, pydantic, uvicorn, httpx to the [options.extras_require] api extra in setup.cfg.
```

Commands Run
    1.    PYTHONPATH=. pytest -q
    2.    PYTHONPATH=. pytest tests/integration -q
    3.    PYTHONPATH=. pytest tests/api -q

Results Summary

1. PYTHONPATH=. pytest -q
    •    Status: ❌
    •    Summary:
    •    Total tests: 3951
    •    Failures: 3
    •    Errors: 0
    •    Notes:

TypeErrors raised when calling start_session(request) and missing tools/api_fingerprint.py utility caused API tests to fail within the full suite.


2. PYTHONPATH=. pytest tests/integration -q
    •    Status: ✅
    •    Summary:
    •    Total tests: 3500
    •    Failures: 0
    •    Errors: 0
    •    Notes:

All integration tests passed.


3. PYTHONPATH=. pytest tests/api -q
    •    Status: ❌
    •    Summary:
    •    Total tests: 49
    •    Failures: 3
    •    Errors: 0
    •    Notes:

Same start_session TypeErrors and missing fingerprint script caused API-specific test failures.


Detailed Failures (If Any)

If any tests failed or errored, include a concise extract here:

•    tests/api/test_baseline_smoke.py::test_start_session_echoes_profile_and_seed — TypeError: start_session() takes 0 positional arguments but 1 was given
•    tests/api/test_baseline_smoke.py::test_fingerprint_script_runs — AssertionError: fingerprint output not produced because tools/api_fingerprint.py is missing (return code 2)
•    tests/api/test_error_contract.py::test_bad_args_seed_type — TypeError: start_session() takes 0 positional arguments but 1 was given

If there were no failures:

N/A — failures are listed above.

Notes and Follow-Ups
    •    Dependency notes:

Added httpx via pip install and included fastapi, pydantic, uvicorn, httpx in the api extra so that `pip install -e .[api]` provides FastAPI testing dependencies.


    •    Open questions / TODOs:

- API start_session callable currently rejects request payload arguments; API tests expect a request parameter.
- tools/api_fingerprint.py is missing, causing baseline smoke fingerprint test to fail.

---
