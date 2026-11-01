package org.intentionspace.inventory.reservation;

import java.time.Instant;
import java.util.UUID;
import org.intentionspace.inventory.config.InventoryProperties;
import org.intentionspace.inventory.stock.StockItem;
import org.intentionspace.inventory.stock.StockItemRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ReservationService {
    private final ReservationRepository reservations;
    private final StockItemRepository stockItems;
    private final InventoryProperties properties;

    public ReservationService(ReservationRepository reservations, StockItemRepository stockItems, InventoryProperties properties) {
        this.reservations = reservations;
        this.stockItems = stockItems;
        this.properties = properties;
    }

    public record ReservationOutcome(Reservation reservation, boolean replayed) { }

    @Transactional
    public ReservationOutcome reserve(CreateReservationRequest request, String idempotencyKey) {
        var byKey = reservations.findByIdempotencyKey(idempotencyKey);
        if (byKey.isPresent()) {
            Reservation existing = byKey.get();
            if (!existing.getOrderId().equals(request.orderId()) || !existing.getSku().equals(request.sku())
                    || existing.getQuantity() != request.quantity()) {
                throw new InventoryException(HttpStatus.CONFLICT, "IDEMPOTENCY_CONFLICT", "Idempotency key belongs to a different reservation request");
            }
            return new ReservationOutcome(existing, true);
        }
        var byOrder = reservations.findByOrderId(request.orderId());
        if (byOrder.isPresent()) {
            return new ReservationOutcome(byOrder.get(), true);
        }

        injectFailureBeforeEffect();
        StockItem item = stockItems.findBySkuForUpdate(request.sku())
            .orElseThrow(() -> new InventoryException(HttpStatus.NOT_FOUND, "SKU_NOT_FOUND", "SKU is not stocked", 0));
        if (item.getAvailableQuantity() < request.quantity()) {
            throw new InventoryException(
                HttpStatus.CONFLICT, "INSUFFICIENT_STOCK", "Requested quantity exceeds available stock",
                item.getAvailableQuantity()
            );
        }
        item.reserve(request.quantity());
        stockItems.save(item);
        String reservationId = "RSV-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12).toUpperCase();
        Reservation reservation = new Reservation(
            reservationId, request.orderId(), idempotencyKey, request.sku(), request.quantity(), Instant.now()
        );
        return new ReservationOutcome(reservations.save(reservation), false);
    }

    private void injectFailureBeforeEffect() {
        String mode = properties.getFailureMode().toLowerCase();
        if (mode.equals("unavailable")) {
            throw new InventoryException(HttpStatus.SERVICE_UNAVAILABLE, "INJECTED_UNAVAILABLE", "Inventory failure injection is enabled");
        }
        if (mode.equals("slow")) {
            try {
                Thread.sleep(properties.getFailureDelayMs());
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                throw new InventoryException(HttpStatus.SERVICE_UNAVAILABLE, "INTERRUPTED", "Reservation processing was interrupted");
            }
        }
    }

    @Transactional(readOnly = true)
    public Reservation get(String reservationId) {
        return reservations.findById(reservationId)
            .orElseThrow(() -> new InventoryException(HttpStatus.NOT_FOUND, "RESERVATION_NOT_FOUND", "Reservation does not exist"));
    }
}
