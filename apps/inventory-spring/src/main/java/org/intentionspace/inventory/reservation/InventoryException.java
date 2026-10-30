package org.intentionspace.inventory.reservation;

import org.springframework.http.HttpStatus;

public class InventoryException extends RuntimeException {
    private final HttpStatus status;
    private final String code;
    private final Integer availableQuantity;

    public InventoryException(HttpStatus status, String code, String message) {
        this(status, code, message, null);
    }

    public InventoryException(HttpStatus status, String code, String message, Integer availableQuantity) {
        super(message);
        this.status = status;
        this.code = code;
        this.availableQuantity = availableQuantity;
    }

    public HttpStatus getStatus() { return status; }
    public String getCode() { return code; }
    public Integer getAvailableQuantity() { return availableQuantity; }
}
