package org.intentionspace.inventory.reservation;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

public record CreateReservationRequest(
    @NotBlank String orderId,
    @NotBlank String sku,
    @Min(1) @Max(1000) int quantity
) {
}
