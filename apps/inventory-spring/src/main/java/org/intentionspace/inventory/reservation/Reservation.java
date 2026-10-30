package org.intentionspace.inventory.reservation;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Version;
import java.time.Instant;

@Entity
@Table(name = "inventory_reservations")
public class Reservation {
    @Id
    private String id;

    @Column(nullable = false, unique = true)
    private String orderId;

    @Column(nullable = false, unique = true)
    private String idempotencyKey;

    @Column(nullable = false)
    private String sku;

    @Column(nullable = false)
    private int quantity;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ReservationStatus status;

    @Column(nullable = false)
    private Instant createdAt;

    @Column(nullable = false)
    private Instant expiresAt;

    @Version
    private long version;

    protected Reservation() {
    }

    public Reservation(String id, String orderId, String idempotencyKey, String sku, int quantity, Instant createdAt) {
        this.id = id;
        this.orderId = orderId;
        this.idempotencyKey = idempotencyKey;
        this.sku = sku;
        this.quantity = quantity;
        this.status = ReservationStatus.RESERVED;
        this.createdAt = createdAt;
        this.expiresAt = createdAt.plusSeconds(15 * 60);
    }

    public String getId() { return id; }
    public String getOrderId() { return orderId; }
    public String getIdempotencyKey() { return idempotencyKey; }
    public String getSku() { return sku; }
    public int getQuantity() { return quantity; }
    public ReservationStatus getStatus() { return status; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getExpiresAt() { return expiresAt; }
}
