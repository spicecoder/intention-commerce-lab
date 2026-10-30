package org.intentionspace.inventory.stock;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Version;

@Entity
@Table(name = "stock_items")
public class StockItem {
    @Id
    private String sku;

    @Column(nullable = false)
    private int availableQuantity;

    @Column(nullable = false)
    private int reservedQuantity;

    @Version
    private long version;

    protected StockItem() {
    }

    public StockItem(String sku, int availableQuantity) {
        this.sku = sku;
        this.availableQuantity = availableQuantity;
        this.reservedQuantity = 0;
    }

    public void reserve(int quantity) {
        if (quantity <= 0 || availableQuantity < quantity) {
            throw new IllegalArgumentException("Insufficient available stock");
        }
        availableQuantity -= quantity;
        reservedQuantity += quantity;
    }

    public String getSku() { return sku; }
    public int getAvailableQuantity() { return availableQuantity; }
    public int getReservedQuantity() { return reservedQuantity; }
    public long getVersion() { return version; }
}
