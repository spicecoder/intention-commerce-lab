package org.intentionspace.inventory.reservation;

import java.time.Instant;

public record ReservationResponse(
    String reservationId,
    String orderId,
    String sku,
    int quantity,
    String reservationStatus,
    String failureReason,
    Instant createdAt,
    Instant expiresAt
) {
    public static ReservationResponse from(Reservation reservation) {
        return new ReservationResponse(
            reservation.getId(), reservation.getOrderId(), reservation.getSku(),
            reservation.getQuantity(), reservation.getStatus().name(), "",
            reservation.getCreatedAt(), reservation.getExpiresAt()
        );
    }
}
