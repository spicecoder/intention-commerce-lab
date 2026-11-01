import { createApp } from './app.js';
import { MemoryOrderRepository, OrderService } from './domain.js';
import { PostgresOrderRepository } from './postgresRepository.js';

const port = Number(process.env.PORT || 3001);
let repository;
if (process.env.DATABASE_URL) {
  repository = new PostgresOrderRepository(process.env.DATABASE_URL);
  let lastError;
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      await repository.init();
      lastError = null;
      break;
    } catch (error) {
      lastError = error;
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  if (lastError) throw lastError;
} else {
  console.warn('DATABASE_URL is not set; using volatile in-memory Orders storage for local development');
  repository = new MemoryOrderRepository();
}

const app = createApp(new OrderService(repository));
const server = app.listen(port, () => console.log(`Orders listening on port ${port}`));
async function shutdown() {
  server.close(async () => {
    if (repository.close) await repository.close();
    process.exit(0);
  });
}
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
