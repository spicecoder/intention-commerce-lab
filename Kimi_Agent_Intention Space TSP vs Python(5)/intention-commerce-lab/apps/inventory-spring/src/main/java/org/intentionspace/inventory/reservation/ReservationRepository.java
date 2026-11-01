package org.intentionspace.inventory.reservation;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ReservationRepository extends JpaRepository<Reservation, String> {
    Optional<Reservation> findByOrderId(String orderId);
    Optional<Reservation> findByIdempotencyKey(String idempotencyKey);
}
