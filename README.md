# Intention Commerce Lab

A runnable reference repository for **governed multi-step agency over fallible enterprise software**. A bounded commerce agent activates contract-checked Design Neurons (DNs); the DNs invoke either prototypes or real Node.js and Spring Boot applications. The LLM is an optional policy participant, not the complete agent.

The executable milestone is:

```text
S_CreateDraft
  → DN_OrdersDraft → S_DraftReady
  → DN_OrdersSubmit → S_ReservationRequested
  → DN_InventoryReserve → S_ReservationDecision
  → DN_OrdersDecide → S_OrderDecision
```

The original CRM, Orders, Inventory, and Shipping reference contracts are retained under `contracts/references/`. CRM and Shipping are intentionally outside this first runtime milestone.

## What is implemented

- **Orders:** Node.js 20, Express, PostgreSQL or volatile local storage, server-side pricing, customer shipping profiles, idempotent drafts, optimistic concurrency, guarded order transitions, and correlation IDs.
- **Inventory:** Java 17, Spring Boot, JPA, PostgreSQL or local H2, transactional reservations, pessimistic stock locking, idempotency by order and request key, stock conflict responses, and correlation IDs.
- **DN runtime:** dependency-free Python 3.11+, exact Signal/intention/Pulse validation, one designated input and output Signal per activation, and returning Y/U/N resolution propagation.
- **Agent:** deterministic policy for engine tests, local Ollama, or an OpenAI-compatible API client. The policy can select only registered DNs and declared arguments.
- **Evidence:** one JSONL event per activation with a unique situated address, input/output Signals, resolution, timestamps, correlation ID, and errors.
- **Failures:** insufficient stock, duplicate reservations, invalid order transitions, unavailable Inventory, slow Inventory, malformed LLM actions, and premature LLM completion.

The framework does **not** make the applications or LLM infallible. It makes declared contracts, resolutions, and activation evidence explicit so some failures cannot silently become business effects.

## Quick start: no services or LLM required

Requires Python 3.11 or later.

```bash
python3 -m intention_commerce.cli --scenario success
python3 -m intention_commerce.cli --scenario insufficient
python3 -m intention_commerce.cli --scenario timeout
```

Expected outcomes:

| Scenario | Reservation resolution | Order outcome |
|---|---:|---|
| `success` | Y | `confirmed` |
| `insufficient` | N | `rejected` |
| `timeout` | U | `pending_review` |

Provenance is written to `provenance/`. A situated address looks like:

```text
U01/C04/IS_CommerceReference/SIT-ORDER-001/DN_InventoryReserve/α03
```

**Scripted runs validate engine mechanics only. They do not evaluate LLM behavior or establish comparative guardrail effectiveness.**

## Run the real applications with Docker

Requires Docker with Compose v2.

```bash
docker compose up --build -d
python3 tests/e2e_real.py
```

This starts independent Orders and Inventory PostgreSQL databases and both application services:

- Orders: `http://localhost:3001/health`
- Inventory: `http://localhost:8081/actuator/health/liveness`

Run the agent manually:

```bash
python3 -m intention_commerce.cli --mode real --scenario success
python3 -m intention_commerce.cli --mode real --scenario insufficient
```

Reset the demo databases when needed:

```bash
docker compose down -v
```

The Compose credentials are development-only. Do not use them as production configuration.

### Real failure injection

Start Inventory with definite unavailability:

```bash
INVENTORY_FAILURE_MODE=unavailable docker compose up --build -d inventory
python3 -m intention_commerce.cli --mode real --scenario success
# Expected: pending_review / U
```

Or inject a seven-second delay, exceeding the DN adapter's default five-second HTTP timeout:

```bash
INVENTORY_FAILURE_MODE=slow INVENTORY_FAILURE_DELAY_MS=7000 docker compose up --build -d inventory
python3 -m intention_commerce.cli --mode real --scenario success
# Expected: pending_review / U
```

A slow request can have an ambiguous server-side outcome. The current agent stops at `PENDING_REVIEW`; it does not assume success or automatically retry. Reservation idempotency supports a future reconciliation worker.

Restore normal behavior with `INVENTORY_FAILURE_MODE=none` and recreate Inventory.

## Local real-service development without Docker

Use separate terminals.

```bash
# Orders: volatile in-memory storage when DATABASE_URL is absent
cd apps/orders-node
npm install
npm start
```

```bash
# Inventory: local H2 when DATABASE_URL is absent
cd apps/inventory-spring
./mvnw spring-boot:run
```

Then, from the repository root:

```bash
python3 -m intention_commerce.cli --mode real --scenario success
```

## Use a local Ollama policy

The default model is `gemma3:4b`; override it with `OLLAMA_MODEL` if desired.

```bash
ollama serve
ollama pull gemma3:4b
```

From the repository root:

```bash
python3 -m intention_commerce.cli --client ollama --mode prototype --scenario success
# Add --mode real to operate against the running applications.
```

Defaults:

```text
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

The LLM must return one JSON action. Invalid DN names, undeclared arguments, missing Pulse values, and premature completion are rejected and recorded. Rejected attempts consume a policy step; `--max-steps` bounds the run.

## Use an API-hosted LLM

The client targets OpenAI-compatible chat completions. Moonshot-compatible defaults are provided, but the model identifier and key must come from your provider.

```bash
export API_BASE_URL=https://api.moonshot.ai/v1
export API_MODEL='your-provider-model-id'
export API_KEY='your-secret-key'
python3 -m intention_commerce.cli --client api --mode prototype --scenario success
```

`MOONSHOT_API_KEY` and `OPENAI_API_KEY` are also accepted. Never commit `.env` or API keys.

## Tests

```bash
# Python contract, provenance, workflow, and adversarial-policy tests
python3 -m unittest discover -s tests/python -v

# Orders domain and HTTP tests
cd apps/orders-node && npm test

# Inventory transactional and HTTP tests
cd apps/inventory-spring && ./mvnw test

# Everything except real-service E2E
bash scripts/verify.sh

# Real-service E2E after starting the applications
python3 tests/e2e_real.py
```

No test requires an LLM API key. Live Ollama/API runs are separate behavioral experiments.

## Repository map

```text
apps/
  orders-node/                 Node.js application and tests
  inventory-spring/            Spring Boot application, Maven wrapper, and tests
contracts/
  references/                  Original commerce-browser reference JSON
  spaces/IS_CommerceReference.json
                               Executable S1–S2 registry
intention_commerce/
  models.py                    Pulse, Signal, AdapterResult
  contracts.py                 Contract loading and validation
  dns.py                       Four bounded DN computations
  applications.py              Prototype and bounded HTTP adapters
  agent.py                     Bounded policy loop
  llm.py                       Ollama and API clients
  provenance.py                JSONL activation evidence
  cli.py                       Run entry point
tests/
  python/                      Offline unit and workflow tests
  e2e_real.py                  Real-service black-box checks
compose.yaml                   Applications and independent PostgreSQL databases
provenance/                    Generated runtime evidence
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the activation and resolution rules.

## Current limits

- Only draft, submit, reserve, and decide are executable; shipment and stock commitment are not yet implemented.
- No authentication, authorization service, production secrets manager, schema migration tool, or hardened deployment is included.
- JPA `ddl-auto: update` and the in-memory/local-H2 modes are development conveniences, not production migration strategies.
- JSONL is append-only by convention, not tamper-evident or replicated.
- There is no reservation-expiry reconciler or automatic resolution of U outcomes.
- The repository does not yet include a controlled direct-tool-calling baseline, so it does not by itself demonstrate comparative reliability improvement.
- LLM policies can fail to finish within the step bound. A stopped or pending run is a valid experimental result, not a successful order.
# intention-commerce-lab
