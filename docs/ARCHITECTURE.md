# Architecture and activation rules

## 1. Bounded agent, participating LLM

The agent is the bounded composition of a policy, contract registry, four DNs, application adapters, and provenance recorder. With an LLM policy enabled, the LLM proposes the next DN activation. It receives no generic HTTP, SQL, shell, or database capability.

The application adapters belong to DNs, not to the LLM. Node.js and Spring Boot remain independently fallible applications.

## 2. Pulse and Signal representation

A Pulse is represented as:

```json
{"name":"quantity","Trivalence":"Y","R":1}
```

A Signal contains an intention and a set of Pulses. Consequential output Signals include a returning Pulse named `resolution`. The executable registry separately declares the exact business Pulses required at each DN boundary.

Trivalence meanings in this repository:

- **Y:** resolved observation or successful business effect.
- **N:** definite conflict, such as insufficient stock or an invalid state transition.
- **U:** unresolved, unavailable, timed out, or otherwise unobserved outcome. U never authorizes confirmation.

## 3. One governing Space per situated activation

Every activation is checked against `IS_CommerceReference`. Its address includes Universe `U01`, Colosseum `C04`, the governing Space, situation, DN, and sequence:

```text
U01/C04/IS_CommerceReference/{situation}/{dn}/α{sequence}
```

This milestone does not implement multi-Space membership or cross-Space mapping. The addressing scheme leaves those later experiments explicit rather than implying universal interoperability.

## 4. S1→DN→S2 enforcement

For each activation, the runtime:

1. Constructs the designated input Signal from declared Pulse values.
2. Restores a returning resolution when the preceding output Signal is this DN's input.
3. Validates Signal name, intention, exact Pulse set, and governing Space.
4. Executes only that DN's bounded application call.
5. Constructs a new output Signal; input Pulse Responses are not mutated.
6. Validates the designated output and its returning resolution Pulse.
7. Appends the complete activation record.

An invalid contract is rejected before the application call. An unexpected runtime error is recorded rather than converted into a fabricated successful output.

## 5. HTTP success is not business Y

Transport and business resolution are distinct. For example, Orders can successfully record an N reservation decision with HTTP 200. `HttpOrders.decide_order` therefore preserves the incoming N rather than treating HTTP 200 as Y.

Mappings include:

| Application observation | DN resolution |
|---|---|
| Draft/order/reservation completed | Y |
| Insufficient stock, unknown entity, invalid transition | N |
| HTTP 5xx, connection failure, timeout | U |
| Orders records the reservation decision | Original reservation Y/U/N |

## 6. Prototype-first and real-service runs

The prototype and HTTP adapters satisfy the same DN-facing methods. Changing `--mode prototype` to `--mode real` changes the adapters, not the Signal registry or agent policy.

Prototype tests validate contract and engine behavior. Real-service tests validate adapter and application integration. Neither alone establishes that an LLM will reliably choose the correct sequence.

## 7. Failure containment and remaining ambiguity

- N prevents order confirmation and produces `REJECTED`.
- U prevents automatic confirmation and produces `PENDING_REVIEW`.
- Duplicate reservation requests return the existing reservation without consuming stock twice.
- Terminal Orders decisions cannot be overwritten by a conflicting later decision.
- A delayed Inventory request may still have an unknown server-side outcome; this is why U requires reconciliation rather than inference.

These controls constrain selected silent propagation paths. They do not eliminate software bugs, model hallucinations, data errors, or all unauthorized effects.

## 8. Evidence boundary

Every DN activation records its Signals, resolution, timing, and application correlation ID. Agent-action rejections and final summaries are recorded alongside them. This supports inspection and replay analysis, but the JSONL files are not cryptographically tamper-evident.
