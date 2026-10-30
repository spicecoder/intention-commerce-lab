import { randomUUID } from 'node:crypto';

export class DomainError extends Error {
  constructor(status, code, message, details = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export const catalog = Object.freeze({
  'SKU-LAMP-001': { unitPriceCents: 12900, currency: 'USD' },
  'SKU-RARE-001': { unitPriceCents: 49900, currency: 'USD' },
});

export const customers = Object.freeze({
  'CUST-001': { shippingAddress: '21 Example Street, Kolkata 700001' },
});

export class MemoryOrderRepository {
  constructor() {
    this.orders = new Map();
    this.idempotency = new Map();
  }

  async findById(id) {
    const order = this.orders.get(id);
    return order ? structuredClone(order) : null;
  }

  async findByIdempotencyKey(key) {
    const id = this.idempotency.get(key);
    return id ? this.findById(id) : null;
  }

  async insert(order, key) {
    if (this.idempotency.has(key)) throw new DomainError(409, 'IDEMPOTENCY_CONFLICT', 'Idempotency key already exists');
    this.orders.set(order.orderId, structuredClone(order));
    this.idempotency.set(key, order.orderId);
    return structuredClone(order);
  }

  async save(order) {
    const current = this.orders.get(order.orderId);
    if (!current || current.version !== order.version) {
      throw new DomainError(409, 'CONCURRENT_ORDER_UPDATE', 'Order changed concurrently; reload before retrying');
    }
    const saved = { ...structuredClone(order), version: order.version + 1, updatedAt: new Date().toISOString() };
    this.orders.set(order.orderId, saved);
    return structuredClone(saved);
  }
}

export class OrderService {
  constructor(repository) {
    this.repository = repository;
  }

  async createDraft(input, idempotencyKey) {
    if (!idempotencyKey) throw new DomainError(400, 'IDEMPOTENCY_KEY_REQUIRED', 'Idempotency-Key header is required');
    const existing = await this.repository.findByIdempotencyKey(idempotencyKey);
    if (existing) return { order: existing, replayed: true };
    const { customerId, sku, quantity } = input;
    if (!customers[customerId]) throw new DomainError(422, 'UNKNOWN_CUSTOMER', 'Customer has no ordering profile');
    if (!catalog[sku]) throw new DomainError(422, 'UNKNOWN_SKU', 'SKU is not in the order catalog');
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 1000) {
      throw new DomainError(422, 'INVALID_QUANTITY', 'Quantity must be an integer between 1 and 1000');
    }
    const product = catalog[sku];
    const now = new Date().toISOString();
    const order = {
      orderId: `ORD-${randomUUID().replaceAll('-', '').slice(0, 12).toUpperCase()}`,
      customerId,
      sku,
      quantity,
      unitPriceCents: product.unitPriceCents,
      totalCents: product.unitPriceCents * quantity,
      currency: product.currency,
      shippingAddress: customers[customerId].shippingAddress,
      status: 'DRAFT',
      reservationId: '',
      failureReason: '',
      version: 0,
      createdAt: now,
      updatedAt: now,
    };
    try {
      return { order: await this.repository.insert(order, idempotencyKey), replayed: false };
    } catch (error) {
      if (error.code === '23505' || error.code === 'IDEMPOTENCY_CONFLICT') {
        const replay = await this.repository.findByIdempotencyKey(idempotencyKey);
        if (replay) return { order: replay, replayed: true };
      }
      throw error;
    }
  }

  async get(orderId) {
    const order = await this.repository.findById(orderId);
    if (!order) throw new DomainError(404, 'ORDER_NOT_FOUND', 'Order does not exist');
    return order;
  }

  async submit(orderId) {
    const order = await this.get(orderId);
    if (order.status === 'DRAFT') {
      order.status = 'SUBMITTED';
      return this.repository.save(order);
    }
    if (['SUBMITTED', 'PENDING_REVIEW', 'CONFIRMED'].includes(order.status)) return order;
    throw new DomainError(409, 'INVALID_ORDER_TRANSITION', `Cannot submit an order in ${order.status}`);
  }

  async decide(orderId, input) {
    const order = await this.get(orderId);
    const { resolution, reservationId = '', failureReason = '' } = input;
    if (!['Y', 'U', 'N'].includes(resolution)) {
      throw new DomainError(422, 'INVALID_RESOLUTION', 'Resolution must be Y, U, or N');
    }
    if (resolution === 'Y' && !reservationId) {
      throw new DomainError(422, 'RESERVATION_ID_REQUIRED', 'A Y reservation decision requires reservationId');
    }
    if (!['SUBMITTED', 'PENDING_REVIEW', 'CONFIRMED', 'REJECTED'].includes(order.status)) {
      throw new DomainError(409, 'INVALID_ORDER_TRANSITION', `Cannot decide an order in ${order.status}`);
    }
    const desiredStatus = resolution === 'Y' ? 'CONFIRMED' : resolution === 'N' ? 'REJECTED' : 'PENDING_REVIEW';
    if (['CONFIRMED', 'REJECTED'].includes(order.status)) {
      if (order.status !== desiredStatus) {
        throw new DomainError(409, 'TERMINAL_ORDER_DECISION', `Order is already ${order.status}`);
      }
      return order;
    }
    order.status = desiredStatus;
    order.reservationId = reservationId;
    order.failureReason = failureReason;
    return this.repository.save(order);
  }
}
