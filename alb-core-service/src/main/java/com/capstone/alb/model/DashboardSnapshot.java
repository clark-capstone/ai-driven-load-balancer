package com.capstone.alb.model;

import java.util.List;
import java.util.Map;

public record DashboardSnapshot(
        long totalRequests,
        Map<String, Integer> collectionCounts,
        Map<String, Integer> serverRequestCounts,
        Map<String, Integer> blockedPerServer,
        List<RouteLogEntry> logs
) {
}
