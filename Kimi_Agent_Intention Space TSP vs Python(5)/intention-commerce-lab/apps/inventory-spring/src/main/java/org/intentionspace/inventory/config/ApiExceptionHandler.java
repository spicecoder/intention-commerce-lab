package org.intentionspace.inventory.config;

import jakarta.servlet.http.HttpServletRequest;
import org.intentionspace.inventory.reservation.InventoryException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingRequestHeaderException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(ApiExceptionHandler.class);

    public record ApiError(String code, String message, String correlationId, Integer availableQuantity) { }

    @ExceptionHandler(InventoryException.class)
    public ResponseEntity<ApiError> inventory(InventoryException error, HttpServletRequest request) {
        return ResponseEntity.status(error.getStatus()).body(new ApiError(
            error.getCode(), error.getMessage(), correlationId(request), error.getAvailableQuantity()
        ));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> validation(MethodArgumentNotValidException error, HttpServletRequest request) {
        return ResponseEntity.unprocessableEntity().body(new ApiError(
            "VALIDATION_FAILED", "Reservation request failed validation", correlationId(request), null
        ));
    }

    @ExceptionHandler({MissingRequestHeaderException.class, HttpMessageNotReadableException.class})
    public ResponseEntity<ApiError> malformed(Exception error, HttpServletRequest request) {
        return ResponseEntity.badRequest().body(new ApiError(
            "MALFORMED_REQUEST", "Reservation request is malformed or lacks a required header", correlationId(request), null
        ));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> unexpected(Exception error, HttpServletRequest request) {
        log.error("Unhandled inventory application error", error);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(new ApiError(
            "INTERNAL_ERROR", "Internal inventory application error", correlationId(request), null
        ));
    }

    private static String correlationId(HttpServletRequest request) {
        return String.valueOf(request.getAttribute(CorrelationFilter.ATTRIBUTE));
    }
}
