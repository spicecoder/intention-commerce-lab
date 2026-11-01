# Intention Commerce Lab
## Project Direction and Multi-Agent Design

**Status:** Proposed target architecture for the revised implementation  
**Reference continuity:** `intentionspace.org` commerce illustration and `intention-commerce-lab` v0.1  
**Initial vertical slice:** order draft → order submission → inventory reservation → order decision  
**Applications:** Node.js Orders and Spring Boot Inventory  
**Agent model:** two independently bounded agents, coordinated through explicit semantic contracts  
**Document purpose:** implementation direction and acceptance reference, not a claim that the current runtime is already multi-agent

---

## 1. Executive direction

The project should evolve from a **single CommerceAgent activating four DNs** into a **two-agent commerce system** with independent authority, policy loops, semantic registries, and provenance:

- **OrderingAgent** owns order drafting, submission, and acceptance decisions around the Node.js Orders application.
- **InventoryAgent** owns stock reservation decisions around the Spring Boot Inventory application.
- **EnterpriseOperations Colosseum C04** governs the declared Signal exchanges between their Intention Spaces.
- The **Intention Universe U01** provides addressable coexistence; it does not provide universal trust, a global resolver, or automatic interoperability.

The central architectural change is not “add another LLM.” It is:

> OrderingAgent must request a reservation from InventoryAgent rather than directly activating InventoryAgent’s DN.

The resulting demonstration should show multi-agent communication through coordinated semantic boundaries while preserving the landing page’s main claim: traditional software and LLMs participate without being assumed infallible.

The first revised release remains deliberately narrow. It should prove the request/return path, independent authority, Y/U/N propagation, idempotency, and end-to-end provenance before adding recommendation, shipment, or self-construction features.

---

## 2. Continuity with the landing page

The landing page already establishes the conceptual reference:

| Landing-page concept | Revised runtime realization |
|---|---|
| Cooperation without assumed reliability | Two agents and two fallible applications with explicit resolutions |
| Semantic boundary | Versioned local Intention Space registry governing each situated DN activation |
| One designated input and output Signal per DN | Contract-validated S1→DN→S2 activation in each agent |
| Enterprise software participates | Node.js and Spring Boot retain independent state and business logic |
| Prototype-ready DN interface | Each agent runs against prototype adapters before real HTTP adapters |
| Intention Colosseum | C04 registers member Space versions and explicit C–MAP exchanges |
| Intention Universe | U01 addresses C04 without implying global authority |
| Pulse provenance | Local activation records linked by Colosseum exchange records |
| Y/U/N resolution | Y reserves, N rejects, U blocks confirmation and requires review/reconciliation |

`IS_CommerceReference` remains the **reference vocabulary and commerce trace** used by the landing page. The revised runtime introduces operational, versioned derivatives:

```text
IS_OrderManagement / v1
IS_InventoryManagement / v1
```

These are not silent edits to the reference. They are explicitly versioned operational contracts, registered in C04.

The full landing-page scenario remains the longer-term path:

```text
CRM → Inventory read → CRM recommendation → Orders draft → Orders submit
→ Inventory reserve → Orders decide → Shipping prepare → Shipping dispatch
→ Inventory commit → Orders complete → CRM close
```

The revised implementation milestone covers only the four central order/reservation activations.

---

## 3. Current baseline and honest architectural gap

The current repository provides useful infrastructure:

- Pulse and Signal values;
- exact contract validation;
- four DN computations;
- prototype and real application adapters;
- scripted, Ollama, and API-hosted policy options;
- JSONL activation provenance;
- idempotent order and reservation behavior;
- Y/U/N business outcomes.

However, it currently has one `CommerceAgent`, one policy loop, one execution context, and one kernel that directly activates `DN_InventoryReserve`.

Therefore, the current implementation is:

> **Single-agent, multi-DN, multi-service integration.**

It is not yet evidence of independent multi-agent cooperation. Node.js, Spring Boot, DNs, and an LLM are not individually agents under the project definition.

The revised implementation must close this gap structurally, not merely change documentation or labels.

Operational debugging of the current local run is intentionally outside this design document.

---

## 4. Goals and non-goals

### 4.1 Goals for the revised vertical slice

1. Establish independent OrderingAgent and InventoryAgent boundaries.
2. Give each agent its own goal, admission rules, policy, DN registry, context, and provenance.
3. Replace direct cross-domain DN activation with declared agent-to-agent Signal exchange.
4. Govern each situated DN activation by exactly one local Intention Space and version.
5. Govern cross-Space exchange through versioned C04 C–MAPs.
6. Preserve Y/U/N through transport and application boundaries.
7. Prevent U from becoming confirmation and N from becoming success.
8. Preserve idempotency and avoid duplicate stock effects.
9. Support deterministic tests and optional local/API LLM policies independently for each agent.
10. Demonstrate the same contracts against prototype and real application adapters.
11. Produce inspectable end-to-end provenance without assuming a shared database or global transaction.

### 4.2 Non-goals for this milestone

- Full recommendation-to-shipment completion;
- autonomous generation of production implementations from documents;
- universal semantic interoperability;
- a global trust or resolution authority;
- distributed ACID transactions across Orders and Inventory;
- automatic recovery of every timeout;
- proof that DN mediation improves every LLM’s reliability;
- production authentication, deployment, or tamper-evident audit storage;
- unrestricted agent access to HTTP, SQL, shell, or database interfaces.

---

## 5. Normative architectural invariants

The following rules are requirements for the revised implementation.

### 5.1 Agent boundary

An agent is a named, bounded composition of conformant DNs, explicit Signal paths, authority, resolutions, policy, and provenance. An LLM may participate as a policy but is not the complete agent.

### 5.2 DN boundary

Each DN activation has exactly one designated input Signal and one designated output Signal. The contract declares the Signal names, intentions, required Pulses, authority, and resolution behavior.

### 5.3 Pulse computation

Only DN computation may change Pulse Responses. Agents, registries, transport adapters, and C–MAPs may construct, project, copy, or rename declared Pulse envelopes, but must not silently rewrite response values.

A unit conversion or semantic transformation that changes a value is computation and therefore requires a declared DN; it cannot be hidden inside a C–MAP.

### 5.4 Returning resolution

Every consequential exchange includes a returning resolution Pulse. When an output Signal becomes a subsequent input Signal, its Y/U/N resolution must be preserved explicitly.

Transport success is not business resolution. HTTP 200 can record a business N decision without converting it to Y.

### 5.5 Situated governance

Every DN activation has exactly one governing Space and version. A reusable DN implementation may participate in multiple Spaces, but no activation has ambiguous or multiple simultaneous governors.

### 5.6 Colosseum exchange

C04 governs exchanges between member Spaces. It does not replace the local governor inside either DN and does not grant implicit authority.

### 5.7 Fallible participants

Node.js, Spring Boot, adapters, policies, and LLMs are fallible. The architecture constrains selected silent propagation paths; it does not eliminate bugs, hallucinations, stale data, or all unauthorized effects.

### 5.8 No undeclared side channels

Agents must not bypass DNs or C–MAPs through direct database access, generic URLs, shared mutable application state, private queues, or undocumented callbacks.

---

## 6. Target system context

```text
                              Universe U01
                                  │
                    Colosseum C04 / EnterpriseOperations
                                  │
             ┌────────────────────┴────────────────────┐
             │                                         │
  IS_OrderManagement / v1                  IS_InventoryManagement / v1
             │                                         │
      OrderingAgent                               InventoryAgent
  goal, policy, authority                       goal, policy, authority
  context, provenance                           context, provenance
             │                                         │
   DN_OrdersDraft                              DN_InventoryReserve
   DN_OrdersSubmit                                     │
   DN_OrdersDecide                             bounded HTTP adapter
             │                                         │
      bounded HTTP adapter                      Spring Boot Inventory
             │                                    reservations + stock DB
      Node.js Orders
       orders + order DB
             │                                         │
             └──── S_ReservationRequested ────────────→│
                    C–MAP-01 / request                 │
             │←─── S_ReservationDecision ──────────────┘
                    C–MAP-02 / return
```

OrderingAgent never invokes `DN_InventoryReserve` directly. It submits a declared Signal to C04. InventoryAgent independently admits or rejects the request and decides whether its DN should be activated.

The applications do not share tables, repositories, or database credentials.

---

## 7. Agent responsibility and authority matrix

| Boundary | OrderingAgent | InventoryAgent |
|---|---|---|
| Primary goal | Produce a resolved order decision | Produce a resolved stock reservation decision |
| Application | Node.js Orders | Spring Boot Inventory |
| DNs | `DN_OrdersDraft`, `DN_OrdersSubmit`, `DN_OrdersDecide` | `DN_InventoryReserve` |
| Owns | Order identity, customer order context, pricing, shipping address, order status | SKU stock, reservation identity, available/reserved quantity, reservation status |
| May request | Stock reservation | No order-state change |
| May return | Order decision to the initiating operator/workflow | Reservation decision to OrderingAgent |
| Cannot | Modify stock, create reservation IDs, activate Inventory DNs | Modify orders, calculate order price, confirm orders |
| Policy | Scripted, Ollama, or API | Scripted, Ollama, or API; independently selectable |
| Failure authority | Mark order rejected or pending review | Return N for definite conflict or U for unresolved observation |

An LLM policy can propose only a registered local DN activation or a declared outbound Signal. It cannot create a new capability by naming an arbitrary URL or DN.

---

## 8. Versioned semantic boundaries

Each local Space registry must define:

1. Space identifier and immutable version;
2. Pulse names, meanings, and response schemas;
3. intention names and purposes;
4. DN input/output Signal pairs;
5. required Pulse sets;
6. returning resolution behavior;
7. application adapter binding;
8. agent authority and permitted exchange roles;
9. conformance tests;
10. source or reference contract lineage.

Natural-language names make the contracts inspectable by people and comparatively accessible to LLMs. They do not guarantee shared understanding. DN validation and application behavior provide the operational guardrail.

### 8.1 Operational contract refinement

The landing-page reference sends the complete order context to Inventory. The revised operational v1 should minimize the cross-Space exchange:

**C04 request projection**

```text
S_ReservationRequested
required Pulses: order_id, sku, quantity
resolution: supplied by the requesting exchange context
```

**C04 return projection**

```text
S_ReservationDecision
required Pulses: order_id, reservation_id, reservation_status, failure_reason
returning resolution Pulse: Y, U, or N
```

OrderingAgent retains customer, price, currency, and shipping context locally. If `DN_OrdersDecide` still requires the full reference Pulse set, OrderingAgent constructs its local input from the returned projection plus its own existing order context. It must not ask Inventory to echo data Inventory does not need.

This is a versioned contract refinement, not an undocumented modification of `IS_CommerceReference`.

---

## 9. DN contract inventory for the vertical slice

### 9.1 IS_OrderManagement / v1

| DN | Input Signal | Output Signal | Required business effect |
|---|---|---|---|
| `DN_OrdersDraft` | `S_CreateDraft` | `S_DraftReady` | Create an idempotent priced draft through Orders |
| `DN_OrdersSubmit` | `S_SubmitOrder` | `S_ReservationRequested` | Submit a valid draft and expose reservation-request context |
| `DN_OrdersDecide` | `S_ReservationDecision` | `S_OrderDecision` | Record confirmed, rejected, or pending-review order decision |

### 9.2 IS_InventoryManagement / v1

| DN | Input Signal | Output Signal | Required business effect |
|---|---|---|---|
| `DN_InventoryReserve` | `S_ReservationRequested` | `S_ReservationDecision` | Reserve stock idempotently or return an explicit conflict/unresolved result |

### 9.3 Required resolution behavior

| Observation | Output resolution | Permitted downstream effect |
|---|---|---|
| Draft created | Y | Order may be submitted |
| Submitted order recorded | Y | Reservation request may be emitted |
| Reservation created or existing idempotent reservation found | Y | Order may be confirmed |
| Insufficient stock or definite invalid request | N | Order may be rejected; never confirmed |
| Inventory unavailable, timeout, or ambiguous outcome | U | Order enters/remains pending review |
| HTTP 200 while recording N | N | Preserve business N |
| Missing required Pulse or wrong intention | Contract rejection | No application call |

---

## 10. Colosseum C04 design

C04 is a governed collection of member Space versions, not a merged vocabulary.

### 10.1 C04 registry contents

```text
Colosseum: C04
Version: v1
Universe: U01
Purpose: order-to-reservation cooperation
Members:
  IS_OrderManagement / v1 — OrderingAgent role
  IS_InventoryManagement / v1 — InventoryAgent role
Mappings:
  C–MAP-01 — reservation request
  C–MAP-02 — reservation decision
Rules:
  admission, authority, resolution preservation, idempotency, provenance
```

### 10.2 C–MAP-01: reservation request

```text
Source: IS_OrderManagement / v1 / S_ReservationRequested
Target: IS_InventoryManagement / v1 / S_ReservationRequested

order_id → order_id
sku      → sku
quantity → quantity
resolution → request context resolution
```

The exchange is valid only when:

- both exact Space versions are registered;
- OrderingAgent holds the requester role;
- the Signal name and intention match;
- all required Pulses are present;
- no undeclared business Pulses or capabilities are introduced;
- the exchange has an idempotency key and correlation identity.

### 10.3 C–MAP-02: reservation decision

```text
Source: IS_InventoryManagement / v1 / S_ReservationDecision
Target: IS_OrderManagement / v1 / S_ReservationDecision

order_id           → order_id
reservation_id     → reservation_id
reservation_status → reservation_status
failure_reason     → failure_reason
resolution         → resolution, unchanged
```

C–MAP-02 must not upgrade U or N to Y. It must not invent a missing reservation ID or discard a failure reason.

### 10.4 Version changes

A Space version change does not automatically propagate into C04. Compatibility must be reassessed and a new C04 version committed. Existing situations continue to identify the versions under which they began.

---

## 11. Communication envelope and provenance identity

Transport metadata is distinct from business Pulses. Each exchange envelope should contain:

```json
{
  "exchange_id": "EX-…",
  "situation_id": "SIT-ORDER-…",
  "colosseum": "C04",
  "colosseum_version": "v1",
  "mapping": "C-MAP-01",
  "source_space": "IS_OrderManagement",
  "source_space_version": "v1",
  "target_space": "IS_InventoryManagement",
  "target_space_version": "v1",
  "idempotency_key": "ORD-…:reservation",
  "correlation_id": "COR-…",
  "causation_id": "EX-or-activation-…",
  "signal": {}
}
```

The envelope routes and audits the exchange. It must not become an undeclared side channel for business values.

Each exchange has a request and return path. A missing return is not success; it leaves the cooperation unresolved.

---

## 12. End-to-end coordination sequence

1. OrderingAgent receives the bounded goal: customer, SKU, and quantity.
2. `DN_OrdersDraft` validates `S_CreateDraft`, invokes Node.js Orders, and emits `S_DraftReady`.
3. `DN_OrdersSubmit` validates `S_SubmitOrder`, submits the order, and emits `S_ReservationRequested`.
4. OrderingAgent requests C–MAP-01; it does not activate an Inventory DN.
5. C04 validates mapping, versions, role, envelope, and Signal shape.
6. InventoryAgent applies its admission policy. A rejection is recorded without a stock effect.
7. For an admitted request, InventoryAgent activates `DN_InventoryReserve` under `IS_InventoryManagement/v1`.
8. The DN invokes Spring Boot Inventory and emits `S_ReservationDecision` with Y, N, or U.
9. InventoryAgent returns that Signal through C–MAP-02.
10. C04 validates the return mapping and preserves resolution.
11. OrderingAgent constructs the local input for `DN_OrdersDecide` from the return projection and local order context.
12. `DN_OrdersDecide` records the order decision through Node.js Orders and emits `S_OrderDecision`.
13. Each agent writes local provenance; C04 writes exchange provenance linked by exchange and correlation IDs.

No shared mutable agent context is required. The complete trace is reconstructed from linked records.

---

## 13. Engineered guardrail layers

| Layer | Guardrail | Example prevented effect | Residual limitation |
|---|---|---|---|
| Policy | Step budget and strict action schema | Endless loop or arbitrary tool call | LLM may still fail to finish |
| Agent admission | Goal, role, and exchange authority | Orders modifying Inventory directly | Policy configuration may be wrong |
| Contract registry | Exact Space version, Signal, intention, Pulse set | Wrong-version or malformed activation | Valid data can still be semantically wrong |
| DN | Bounded computation and designated output | Hidden side effect or invented return channel | DN implementation may contain bugs |
| C–MAP | Declared projection and resolution preservation | U silently becoming Y | Mapping definition may be incomplete |
| Orders state machine | Guarded transitions and terminal-state protection | Rejected order becoming confirmed without reservation | Application logic can still be defective |
| Inventory transaction | Locked stock update and reservation | Overselling during concurrent requests | Database and operational faults remain |
| Idempotency | Stable order/reservation request identity | Duplicate stock consumption | Ambiguous first attempt may require reconciliation |
| Provenance | Local and exchange evidence | Silent untraceable effect | JSONL is not tamper-evident |
| Prototype binding | Contract-compatible adapter substitution | Agent coupled directly to a real URL | Prototype success does not prove real-service correctness |

The design claim is therefore precise:

> Guardrails make selected violations and unresolved outcomes explicit and block specified unauthorized transitions. They do not establish infallibility.

---

## 14. Failure and reconciliation semantics

### 14.1 Definite conflict: N

Examples include insufficient stock, unknown SKU, invalid order state, wrong contract version, and explicit admission denial where denial is definite and policy-based.

The system must record the reason and prevent confirmation. N does not mean temporary unavailability.

### 14.2 Unresolved outcome: U

Examples include timeout, connection failure, HTTP 5xx, missing observation, and an application outcome that cannot be established.

U must not be retried blindly as though no effect occurred. A timeout can happen after Inventory committed a reservation. The initial agent run should stop at `PENDING_REVIEW`.

A later reconciliation function may:

1. query by the stable order/reservation idempotency identity;
2. return the existing reservation if found;
3. return U again if the outcome remains unobservable;
4. never create a second reservation for the same order.

Reconciliation is a separate declared workflow, not a hidden retry loop.

### 14.3 Compensation and expiry

Reservation release, expiry, shipment dispatch, and stock commitment are outside the first vertical slice. They must be added as explicit DNs and Signals rather than implicit database cleanup.

There is no distributed transaction across Orders and Inventory. Consistency is achieved through explicit states, idempotency, resolution, and later compensation workflows.

---

## 15. Prototype-first implementation path

Each agent must run against local prototypes before real-service adapters are enabled.

```text
OrderingAgent contract tests
├── PrototypeOrders
└── HttpOrders

InventoryAgent contract tests
├── PrototypeInventory
└── HttpInventory
```

C04 also needs a prototype exchange runtime with exactly the same admission and mapping contracts as the networked exchange.

The progression is:

1. validate local DN contracts;
2. validate agent admission and outbound Signals;
3. validate C–MAP request and return contracts;
4. run deterministic two-agent prototype scenarios;
5. run real application adapter contract tests;
6. run real-service two-agent E2E scenarios;
7. enable Ollama/API policies as separate behavioral experiments.

Prototype results validate engine mechanics. They do not prove real-service correctness or LLM policy quality.

---

## 16. Revised repository direction

The current code should be evolved rather than replaced indiscriminately.

```text
intention-commerce-lab/
├── agents/
│   ├── ordering_agent.py
│   └── inventory_agent.py
├── colosseum/
│   ├── exchange.py
│   ├── admission.py
│   └── provenance.py
├── contracts/
│   ├── references/
│   │   ├── CPUX_CRM.json
│   │   ├── CPUX_Inventory.json
│   │   ├── CPUX_Orders.json
│   │   └── CPUX_Shipping.json
│   ├── spaces/
│   │   ├── IS_CommerceReference.json
│   │   ├── IS_OrderManagement.v1.json
│   │   └── IS_InventoryManagement.v1.json
│   └── colosseums/
│       └── C04.v1.json
├── intention_commerce/
│   ├── models.py
│   ├── contracts.py
│   ├── dns.py
│   ├── applications.py
│   ├── agent.py
│   ├── llm.py
│   ├── provenance.py
│   └── cli.py
├── apps/
│   ├── orders-node/
│   └── inventory-spring/
└── tests/
    ├── python/
    ├── colosseum/
    └── e2e_multiagent.py
```

### 16.1 Migration of existing components

| Existing component | Revised use |
|---|---|
| `Pulse`, `Signal`, `AdapterResult` | Reuse unchanged where possible |
| `ContractRegistry` | Instantiate separately for each Space/version |
| `CommerceKernel` | Split into Ordering and Inventory local kernels |
| `CommerceAgent` | Generalize into configurable bounded agent runtime |
| `ScriptedPolicy` | Create deterministic Ordering and Inventory policies |
| `OllamaClient`, `ApiClient` | Reuse independently for either agent |
| `PrototypeOrders`, `HttpOrders` | Reuse behind OrderingAgent |
| `PrototypeInventory`, `HttpInventory` | Reuse behind InventoryAgent |
| `ProvenanceRecorder` | Separate local recorders plus C04 exchange recorder |
| Existing CLI | Add multi-agent scenario runner; retain single-agent mode only as a labeled legacy baseline |

---

## 17. Implementation phases

### Phase 0 — Baseline clarity

- Mark the current runtime as single-agent.
- Freeze the current contract and test baseline.
- Keep runtime defect investigation separate from the target architecture.
- Add this document as the revision reference.

### Phase 1 — Deterministic two-agent prototype

- Split Spaces and local kernels.
- Implement separate agent contexts, admission rules, and provenance.
- Implement C04 v1 and C–MAP-01/02.
- Run success, insufficient-stock, timeout, duplicate, wrong-version, and undeclared-interaction tests.
- Use scripted policies only; establish engine mechanics first.

### Phase 2 — Real Node.js and Spring Boot integration

- Reuse real adapters behind their respective agents.
- Run both applications with independent databases.
- Verify Y/N/U and idempotent reconciliation prerequisites.
- Confirm no cross-agent direct adapter or DN access.

### Phase 3 — Independent optional LLM policies

- Configure each agent separately as scripted, Ollama, or API.
- Test malformed actions, invented IDs, unauthorized exchange attempts, and premature completion.
- Record model/client identity and policy failures without claiming that two LLMs are required.

### Phase 4 — Reconciliation and networked exchange

- Move C04 exchange from in-process messages to a bounded HTTP or messaging transport if needed.
- Add U reconciliation by stable idempotency identity.
- Add authentication, service identity, and transport protections appropriate to deployment.

### Phase 5 — Commerce trace expansion

- Add Shipping and CRM agents/Spaces only when their authority and contracts are defined.
- Add dispatch before stock commit, preserving business causality.
- Extend C04 through new versions and conformance tests.

Document-driven Space and Colosseum construction may later generate candidate registries and prototypes, but it is a separate program and must not be coupled to this first multi-agent milestone.

---

## 18. Verification and acceptance matrix

| ID | Scenario | Required result |
|---|---|---|
| MA-01 | Successful reservation | Inventory returns Y; Orders confirms once |
| MA-02 | Insufficient stock | Inventory returns N; Orders rejects; no stock effect |
| MA-03 | Inventory unavailable | Return U; Orders pending review; never confirmed |
| MA-04 | Inventory timeout after possible effect | Return U; no blind retry; stable identity supports reconciliation |
| MA-05 | Duplicate reservation request | Same reservation returned; stock consumed once |
| MA-06 | OrderingAgent attempts direct Inventory DN activation | Rejected before application call and recorded |
| MA-07 | Undeclared C–MAP or Signal | Rejected by C04; no target effect |
| MA-08 | Wrong Space or C04 version | Rejected as incompatible; no silent upgrade |
| MA-09 | HTTP 200 records N decision | Final business resolution remains N |
| MA-10 | C–MAP attempts to change U/N to Y | Contract violation; exchange rejected |
| MA-11 | LLM supplies URL, SQL, unknown DN, or invented reservation ID | Rejected; no undeclared capability or confirmation |
| MA-12 | InventoryAgent admission denial | No Inventory DN activation or stock effect; denial traced |
| MA-13 | Independent policy selection | Either agent can run scripted/Ollama/API without changing contracts |
| MA-14 | Prototype to real adapter switch | Same agent Signals and C–MAPs; only bindings change |
| MA-15 | End-to-end provenance | Both local DN activations and both C–MAP directions are linked |
| MA-16 | Agent isolation | No shared mutable context, DB credential, or application repository |
| MA-17 | Step budget exhaustion | Run stops unresolved; never fabricates success |
| MA-18 | Application defect | Failure is observed and contained where specified; not claimed impossible |

### Minimum definition of done for the revised vertical slice

The implementation is ready to demonstrate only when:

1. MA-01 through MA-15 pass deterministically.
2. The current single-agent path is labeled as a baseline, not presented as multi-agent.
3. OrderingAgent has no code path that directly activates `DN_InventoryReserve`.
4. InventoryAgent can admit or reject a request independently.
5. Both local Spaces and C04 are versioned.
6. Real Node.js and Spring Boot runs pass success, N, and U scenarios.
7. The trace links request and return exchanges to local DN activation records.
8. Documentation states residual limits and distinguishes scripted, prototype, real-service, and live-LLM evidence.

---

## 19. Experimental evaluation direction

After functional correctness, the repository can support a controlled comparison:

```text
A. Direct application tool calling
B. Single-agent DN mediation
C. Multi-agent DN + Colosseum mediation
```

Hold the task set, application state, fault injection, model, and step budget as constant as practical. Measure:

- task completion;
- unauthorized effects;
- malformed contract attempts;
- incorrect U/N handling;
- duplicate stock effects;
- provenance completeness;
- reconciliation success;
- policy steps and failures.

The comparison should report negative and null results. The architecture’s presence alone is not evidence of comparative improvement.

---

## 20. Principal design decisions

The revised implementation should proceed with these defaults unless a later design review changes them:

1. **Two agents, not two LLM personas.** Independent authority and execution boundaries define the agents.
2. **Two operational Spaces, coordinated by C04.** This demonstrates a real Colosseum rather than only an address prefix.
3. **Versioned contracts.** No silent adoption of changed Space semantics.
4. **Narrow cross-Space projections.** Inventory receives only what reservation requires.
5. **Scripted determinism first.** LLM behavior is tested after engine mechanics.
6. **Independent prototypes and real adapters.** Contract compatibility precedes integration.
7. **No distributed transaction illusion.** Explicit state and reconciliation handle partial failure.
8. **No automatic retry on U.** Ambiguity requires observation or reconciliation.
9. **Separate local and exchange provenance.** A linked trace replaces shared hidden state.
10. **Narrow initial scope.** Prove reservation cooperation before adding shipment or self-construction.

---

## 21. Project direction statement

The revised commerce application should be a concrete reference for this proposition:

> Independently bounded agents can cooperate across traditional enterprise applications when each local computation is governed by a versioned semantic boundary and each cross-boundary exchange is declared, authorized, resolution-preserving, and traceable.

Node.js and Spring Boot supply realistic business effects and failure modes. DNs supply bounded computation and Signal contracts. Agents supply independent authority and policy. C04 supplies governed cooperation. U01 supplies addressable coexistence without pretending that all Spaces or Colosseums share trust.

The immediate implementation objective is not maximum feature coverage. It is a small, inspectable, testable multi-agent vertical slice whose code path matches the architecture shown on the landing page.
