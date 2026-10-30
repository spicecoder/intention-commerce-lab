package org.intentionspace.inventory.stock;

public record StockResponse(String sku, int availableQuantity, int reservedQuantity, long version) {
    public static StockResponse from(StockItem item) {
        return new StockResponse(item.getSku(), item.getAvailableQuantity(), item.getReservedQuantity(), item.getVersion());
    }
}
