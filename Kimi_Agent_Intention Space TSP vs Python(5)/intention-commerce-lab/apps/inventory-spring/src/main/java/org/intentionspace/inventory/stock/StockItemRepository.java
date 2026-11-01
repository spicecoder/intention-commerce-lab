package org.intentionspace.inventory.stock;

import jakarta.persistence.LockModeType;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface StockItemRepository extends JpaRepository<StockItem, String> {
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select item from StockItem item where item.sku = :sku")
    Optional<StockItem> findBySkuForUpdate(@Param("sku") String sku);
}
