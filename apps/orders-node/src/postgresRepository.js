import pg from 'pg';
import { DomainError } from './domain.js';

const { Pool } = pg;

function mapRow(row) {
  if (!row) return null;
  return {
    orderId: row.id,
    customerId: row.customer_id,
    sku: row.sku,
    quantity: row.quantity,
    unitPriceCents: Number(row.unit_price_cents),
    totalCents: Number(row.total_cents),
    currency: row.currency,
    shippingAddress: row.shipping_address,
    status: row.status,
    reservationId: row.reservation_id,
    failureReason: row.failure_reason,
    version: row.version,
    createdAt: new Date(row.created_at).toISOString(),
    updatedAt: new Date(row.updated_at).toISOString(),
  };
}

export class PostgresOrderRepository {
  constructor(connectionString) {
    this.pool = new Pool({ connectionString });
  }

  async init() {
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        idempotency_key TEXT NOT NULL UNIQUE,
        customer_id TEXT NOT NULL,
        sku TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        unit_price_cents BIGINT NOT NULL,
        total_cents BIGINT NOT NULL,
        currency CHAR(3) NOT NULL,
        shipping_address TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('DRAFT','SUBMITTED','PENDING_REVIEW','CONFIRMED','REJECTED')),
        reservation_id TEXT NOT NULL DEFAULT '',
        failure_reason TEXT NOT NULL DEFAULT '',
        version INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL
      )
    `);
  }

  async findById(id) {
    const result = await this.pool.query('SELECT * FROM orders WHERE id = $1', [id]);
    return mapRow(result.rows[0]);
  }

  async findByIdempotencyKey(key) {
    const result = await this.pool.query('SELECT * FROM orders WHERE idempotency_key = $1', [key]);
    return mapRow(result.rows[0]);
  }

  async insert(order, key) {
    const result = await this.pool.query(`
      INSERT INTO orders (
        id, idempotency_key, customer_id, sku, quantity, unit_price_cents,
        total_cents, currency, shipping_address, status, reservation_id,
        failure_reason, version, created_at, updated_at
      ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
      RETURNING *
    `, [
      order.orderId, key, order.customerId, order.sku, order.quantity,
      order.unitPriceCents, order.totalCents, order.currency,
      order.shippingAddress, order.status, order.reservationId,
      order.failureReason, order.version, order.createdAt, order.updatedAt,
    ]);
    return mapRow(result.rows[0]);
  }

  async save(order) {
    const result = await this.pool.query(`
      UPDATE orders SET
        status = $2, reservation_id = $3, failure_reason = $4,
        version = version + 1, updated_at = NOW()
      WHERE id = $1 AND version = $5
      RETURNING *
    `, [order.orderId, order.status, order.reservationId, order.failureReason, order.version]);
    if (!result.rowCount) {
      throw new DomainError(409, 'CONCURRENT_ORDER_UPDATE', 'Order changed concurrently; reload before retrying');
    }
    return mapRow(result.rows[0]);
  }

  async close() {
    await this.pool.end();
  }
}
