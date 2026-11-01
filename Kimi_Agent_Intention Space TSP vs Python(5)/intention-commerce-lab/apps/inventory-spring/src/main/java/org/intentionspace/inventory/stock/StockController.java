package org.intentionspace.inventory.stock;

import org.intentionspace.inventory.reservation.InventoryException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/inventory/stock")
public class StockController {
    private final StockItemRepository repository;

    public StockController(StockItemRepository repository) {
        this.repository = repository;
    }

    @GetMapping("/{sku}")
    public StockResponse get(@PathVariable String sku) {
        return repository.findById(sku).map(StockResponse::from)
            .orElseThrow(() -> new InventoryException(HttpStatus.NOT_FOUND, "SKU_NOT_FOUND", "SKU is not stocked", 0));
    }
}
