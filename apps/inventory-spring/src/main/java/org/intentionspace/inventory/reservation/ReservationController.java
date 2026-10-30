package org.intentionspace.inventory.reservation;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/inventory/reservations")
public class ReservationController {
    private final ReservationService service;

    public ReservationController(ReservationService service) {
        this.service = service;
    }

    @PostMapping
    public ResponseEntity<ReservationResponse> reserve(
        @Valid @RequestBody CreateReservationRequest request,
        @RequestHeader("Idempotency-Key") String idempotencyKey
    ) {
        if (idempotencyKey.isBlank()) {
            throw new InventoryException(HttpStatus.BAD_REQUEST, "IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key cannot be blank");
        }
        var outcome = service.reserve(request, idempotencyKey);
        return ResponseEntity.status(outcome.replayed() ? HttpStatus.OK : HttpStatus.CREATED)
            .body(ReservationResponse.from(outcome.reservation()));
    }

    @GetMapping("/{reservationId}")
    public ReservationResponse get(@PathVariable String reservationId) {
        return ReservationResponse.from(service.get(reservationId));
    }
}
