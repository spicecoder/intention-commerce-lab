package org.intentionspace.inventory.config;

import org.intentionspace.inventory.stock.StockItem;
import org.intentionspace.inventory.stock.StockItemRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
public class DataInitializer implements CommandLineRunner {
    private final StockItemRepository stockItems;

    public DataInitializer(StockItemRepository stockItems) {
        this.stockItems = stockItems;
    }

    @Override
    @Transactional
    public void run(String... args) {
        if (!stockItems.existsById("SKU-LAMP-001")) {
            stockItems.save(new StockItem("SKU-LAMP-001", 5));
        }
        if (!stockItems.existsById("SKU-RARE-001")) {
            stockItems.save(new StockItem("SKU-RARE-001", 0));
        }
    }
}
