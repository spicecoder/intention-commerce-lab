package org.intentionspace.inventory;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.intentionspace.inventory.config.InventoryProperties;
import org.intentionspace.inventory.reservation.CreateReservationRequest;
import org.intentionspace.inventory.reservation.InventoryException;
import org.intentionspace.inventory.reservation.ReservationRepository;
import org.intentionspace.inventory.reservation.ReservationService;
import org.intentionspace.inventory.stock.StockItemRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class InventoryApplicationTests {
    @Autowired ReservationService service;
    @Autowired StockItemRepository stockItems;
    @Autowired ReservationRepository reservations;
    @Autowired InventoryProperties properties;
    @Autowired MockMvc mockMvc;

    @AfterEach
    void resetFailureInjection() {
        properties.setFailureMode("none");
    }

    @Test
    void successfulReservationDecreasesAvailableStock() {
        var outcome = service.reserve(new CreateReservationRequest("ORD-SUCCESS", "SKU-LAMP-001", 2), "reserve-success");
        assertThat(outcome.replayed()).isFalse();
        assertThat(outcome.reservation().getId()).startsWith("RSV-");
        var stock = stockItems.findById("SKU-LAMP-001").orElseThrow();
        assertThat(stock.getAvailableQuantity()).isEqualTo(3);
        assertThat(stock.getReservedQuantity()).isEqualTo(2);
    }

    @Test
    void duplicateReservationDoesNotConsumeStockTwice() {
        var request = new CreateReservationRequest("ORD-IDEMPOTENT", "SKU-LAMP-001", 1);
        var first = service.reserve(request, "reserve-idempotent");
        var second = service.reserve(request, "reserve-idempotent");
        assertThat(second.replayed()).isTrue();
        assertThat(second.reservation().getId()).isEqualTo(first.reservation().getId());
        assertThat(stockItems.findById("SKU-LAMP-001").orElseThrow().getAvailableQuantity()).isEqualTo(4);
        assertThat(reservations.count()).isEqualTo(1);
    }

    @Test
    void insufficientStockIsDefiniteConflictWithoutStockMutation() {
        assertThatThrownBy(() -> service.reserve(new CreateReservationRequest("ORD-INSUFFICIENT", "SKU-RARE-001", 1), "reserve-insufficient"))
            .isInstanceOfSatisfying(InventoryException.class, error -> {
                assertThat(error.getCode()).isEqualTo("INSUFFICIENT_STOCK");
                assertThat(error.getAvailableQuantity()).isZero();
            });
        assertThat(stockItems.findById("SKU-RARE-001").orElseThrow().getAvailableQuantity()).isZero();
        assertThat(reservations.count()).isZero();
    }

    @Test
    void unavailableFailureOccursBeforeAnyStockEffect() {
        properties.setFailureMode("unavailable");
        assertThatThrownBy(() -> service.reserve(new CreateReservationRequest("ORD-UNAVAILABLE", "SKU-LAMP-001", 1), "reserve-unavailable"))
            .isInstanceOfSatisfying(InventoryException.class, error -> assertThat(error.getCode()).isEqualTo("INJECTED_UNAVAILABLE"));
        assertThat(stockItems.findById("SKU-LAMP-001").orElseThrow().getAvailableQuantity()).isEqualTo(5);
        assertThat(reservations.count()).isZero();
    }

    @Test
    void httpReservationReturnsCorrelationAndReservedStatus() throws Exception {
        mockMvc.perform(post("/api/inventory/reservations")
                .header("Idempotency-Key", "http-reserve")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"orderId\":\"ORD-HTTP\",\"sku\":\"SKU-LAMP-001\",\"quantity\":1}"))
            .andExpect(status().isCreated())
            .andExpect(header().exists("X-Correlation-ID"))
            .andExpect(jsonPath("$.reservationStatus").value("RESERVED"))
            .andExpect(jsonPath("$.reservationId").isNotEmpty());
    }

    @Test
    void insufficientStockMapsToHttpConflict() throws Exception {
        mockMvc.perform(post("/api/inventory/reservations")
                .header("Idempotency-Key", "http-insufficient")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"orderId\":\"ORD-HTTP-N\",\"sku\":\"SKU-RARE-001\",\"quantity\":1}"))
            .andExpect(status().isConflict())
            .andExpect(jsonPath("$.code").value("INSUFFICIENT_STOCK"))
            .andExpect(jsonPath("$.availableQuantity").value(0));
    }
}
