import test from 'node:test';
import assert from 'node:assert/strict';
import { createApp } from '../src/app.js';
import { DomainError, MemoryOrderRepository, OrderService } from '../src/domain.js';

function fixture() {
  return new OrderService(new MemoryOrderRepository());
}

async function submitted(service, key = 'draft-1') {
  const { order } = await service.createDraft({ customerId: 'CUST-001', sku: 'SKU-LAMP-001', quantity: 2 }, key);
  return service.submit(order.orderId);
}

test('draft calculates server-side price and customer shipping address', async () => {
  const service = fixture();
  const { order } = await service.createDraft({ customerId: 'CUST-001', sku: 'SKU-LAMP-001', quantity: 2 }, 'draft-1');
  assert.equal(order.status, 'DRAFT');
  assert.equal(order.unitPriceCents, 12900);
  assert.equal(order.totalCents, 25800);
  assert.match(order.shippingAddress, /Kolkata/);
});

test('draft idempotency returns the original order without duplication', async () => {
  const service = fixture();
  const first = await service.createDraft({ customerId: 'CUST-001', sku: 'SKU-LAMP-001', quantity: 1 }, 'same-key');
  const second = await service.createDraft({ customerId: 'CUST-001', sku: 'SKU-LAMP-001', quantity: 1 }, 'same-key');
  assert.equal(first.order.orderId, second.order.orderId);
  assert.equal(second.replayed, true);
});

test('invalid quantity and unknown SKU are definite application conflicts', async () => {
  const service = fixture();
  await assert.rejects(
    service.createDraft({ customerId: 'CUST-001', sku: 'SKU-LAMP-001', quantity: 0 }, 'bad-qty'),
    error => error instanceof DomainError && error.status === 422 && error.code === 'INVALID_QUANTITY',
  );
  await assert.rejects(
    service.createDraft({ customerId: 'CUST-001', sku: 'NO-SUCH-SKU', quantity: 1 }, 'bad-sku'),
    error => error.code === 'UNKNOWN_SKU',
  );
});

test('Y decision confirms a submitted order and stores reservation', async () => {
  const service = fixture();
  const order = await submitted(service);
  const decided = await service.decide(order.orderId, { resolution: 'Y', reservationId: 'RSV-1', failureReason: '' });
  assert.equal(decided.status, 'CONFIRMED');
  assert.equal(decided.reservationId, 'RSV-1');
});

test('N decision rejects an order without confirming it', async () => {
  const service = fixture();
  const order = await submitted(service);
  const decided = await service.decide(order.orderId, { resolution: 'N', failureReason: 'INSUFFICIENT_STOCK' });
  assert.equal(decided.status, 'REJECTED');
  assert.equal(decided.failureReason, 'INSUFFICIENT_STOCK');
});

test('U decision blocks automatic confirmation', async () => {
  const service = fixture();
  const order = await submitted(service);
  const decided = await service.decide(order.orderId, { resolution: 'U', failureReason: 'TIMEOUT' });
  assert.equal(decided.status, 'PENDING_REVIEW');
});

test('Y decision without reservation evidence is rejected', async () => {
  const service = fixture();
  const order = await submitted(service);
  await assert.rejects(
    service.decide(order.orderId, { resolution: 'Y' }),
    error => error.code === 'RESERVATION_ID_REQUIRED',
  );
});

test('a later conflicting decision cannot overwrite a terminal order', async () => {
  const service = fixture();
  const order = await submitted(service);
  await service.decide(order.orderId, { resolution: 'Y', reservationId: 'RSV-1' });
  await assert.rejects(
    service.decide(order.orderId, { resolution: 'N', failureReason: 'LATE_CONFLICT' }),
    error => error.code === 'TERMINAL_ORDER_DECISION',
  );
});

test('HTTP API exposes correlation IDs and bounded errors', async (t) => {
  const app = createApp(fixture());
  const server = app.listen(0);
  t.after(() => server.close());
  await new Promise(resolve => server.once('listening', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  const created = await fetch(`${base}/api/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Idempotency-Key': 'http-draft' },
    body: JSON.stringify({ customerId: 'CUST-001', sku: 'SKU-LAMP-001', quantity: 1 }),
  });
  assert.equal(created.status, 201);
  assert.ok(created.headers.get('x-correlation-id'));
  const order = await created.json();
  const submittedResponse = await fetch(`${base}/api/orders/${order.orderId}/submit`, { method: 'POST' });
  assert.equal(submittedResponse.status, 200);
  const missing = await fetch(`${base}/api/orders/ORD-MISSING`);
  assert.equal(missing.status, 404);
  assert.equal((await missing.json()).code, 'ORDER_NOT_FOUND');
});
