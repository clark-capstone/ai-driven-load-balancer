package com.capstone.alb.model;

import java.util.Map;

public record RouteLogEntry(
        String id,
        String timestamp,
        String status,
        String collection,
        String confidenceBand,
        double confidence,
        String serverId,
        String serverName,
        String response,
        String reason,
        String sourceIp,
        Map<String, Object> request,
        Map<String, Object> metadata
) {
}
