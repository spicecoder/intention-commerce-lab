import express from 'express';
import { randomUUID } from 'node:crypto';
import { DomainError } from './domain.js';

export function createApp(service) {
  const app = express();
  app.disable('x-powered-by');
  app.use(express.json({ limit: '32kb' }));
  app.use((req, res, next) => {
    req.correlationId = req.get('X-Correlation-ID') || randomUUID();
    res.set('X-Correlation-ID', req.correlationId);
    next();
  });

  app.get('/health', (req, res) => res.json({ status: 'UP', service: 'orders-node' }));

  app.post('/api/orders', async (req, res, next) => {
    try {
      const result = await service.createDraft(req.body, req.get('Idempotency-Key'));
      res.status(result.replayed ? 200 : 201).json(result.order);
    } catch (error) { next(error); }
  });

  app.get('/api/orders/:orderId', async (req, res, next) => {
    try { res.json(await service.get(req.params.orderId)); } catch (error) { next(error); }
  });

  app.post('/api/orders/:orderId/submit', async (req, res, next) => {
    try { res.json(await service.submit(req.params.orderId)); } catch (error) { next(error); }
  });

  app.post('/api/orders/:orderId/reservation-decision', async (req, res, next) => {
    try { res.json(await service.decide(req.params.orderId, req.body)); } catch (error) { next(error); }
  });

  app.use((req, res) => res.status(404).json({ code: 'ROUTE_NOT_FOUND', message: 'Route does not exist' }));
  app.use((error, req, res, next) => {
    const status = error instanceof DomainError ? error.status : error.type === 'entity.parse.failed' ? 400 : 500;
    const code = error.code || (status === 400 ? 'MALFORMED_JSON' : 'INTERNAL_ERROR');
    if (status >= 500) console.error(JSON.stringify({ level: 'ERROR', correlationId: req.correlationId, message: error.message }));
    res.status(status).json({
      code,
      message: status >= 500 ? 'Internal order application error' : error.message,
      correlationId: req.correlationId,
      ...(error.details || {}),
    });
  });
  return app;
}
