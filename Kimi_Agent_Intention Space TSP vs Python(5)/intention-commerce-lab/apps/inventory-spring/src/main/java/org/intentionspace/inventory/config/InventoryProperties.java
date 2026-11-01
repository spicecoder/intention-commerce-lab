package org.intentionspace.inventory.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "inventory")
public class InventoryProperties {
    private String failureMode = "none";
    private long failureDelayMs = 7000;

    public String getFailureMode() { return failureMode; }
    public void setFailureMode(String failureMode) { this.failureMode = failureMode; }
    public long getFailureDelayMs() { return failureDelayMs; }
    public void setFailureDelayMs(long failureDelayMs) { this.failureDelayMs = failureDelayMs; }
}
