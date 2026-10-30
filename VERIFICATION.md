# Verification record

Verified on 2026-10-30.

## Passed

- **18 Python tests:** contracts, Pulse/Signal validation, Y/U/N propagation, prototype workflows, provenance, adversarial policy rejection, and mocked Ollama/API client behavior.
- **9 Node.js tests:** pricing, idempotency, invalid requests, guarded Y/U/N decisions, terminal-state protection, and HTTP behavior.
- **6 Spring Boot tests:** transactional reservation, idempotent retry, insufficient stock, unavailable failure before effects, and HTTP responses.
- **Real-service E2E:** the Python agent called the actual Node.js and Spring Boot HTTP services and produced:
  - success → `confirmed` / Y;
  - insufficient stock → `rejected` / N;
  - unavailable Inventory → `pending_review` / U.
- Python modules compiled successfully.

## Not exercised in this environment

- Docker and Docker Compose were unavailable, so `compose.yaml` was not executed here.
- The real-service E2E used Orders' in-memory repository and Inventory's H2 repository. PostgreSQL containers were not available for a live database integration run.
- No live Ollama or hosted API model was called. Both clients were tested with mocked HTTP responses; live model behavior remains an experiment for the user's environment.

These limits are why the repository claims a verified reference implementation, not production readiness or demonstrated LLM reliability.
