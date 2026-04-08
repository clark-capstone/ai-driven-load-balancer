package com.capstone.alb.model;

public record RouteDecisionResponse(
        String requestId,
        String result,
        String collection,
        String confidenceBand,
        double confidence,
        String selectedServer,
        String selectedServerName,
        long totalRequests,
        String message,
        RouteLogEntry log
) {
}
