package com.capstone.alb.service;

import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import com.capstone.alb.model.SystemMetrics;
import com.capstone.alb.strategy.LoadBalancingStrategy;

@Service
public class RoutingService {

    private static final Logger logger = LoggerFactory.getLogger(RoutingService.class);

    private final LoadBalancingStrategy strategy;
    private final RemoteMetricsService remoteMetricsService;

    public RoutingService(LoadBalancingStrategy strategy,
                          RemoteMetricsService remoteMetricsService) {
        this.strategy = strategy;
        this.remoteMetricsService = remoteMetricsService;
    }

    public String routeRequest() {

        Map<String, SystemMetrics> allMetrics = new HashMap<>();

        try {
            // ✅ 1. Add local node metrics
            SystemMetrics localMetrics = remoteMetricsService.getLocalMetrics();
            if (localMetrics != null) {
                allMetrics.put("LOCAL", localMetrics);
            }

            // ✅ 2. Add remote node metrics
            Map<String, SystemMetrics> remoteMetrics =
                    remoteMetricsService.fetchAllMetrics();

            if (remoteMetrics != null && !remoteMetrics.isEmpty()) {
                allMetrics.putAll(remoteMetrics);
            }

        } catch (Exception e) {
            logger.error("Error fetching metrics: ", e);
        }

        // ❌ No nodes available
        if (allMetrics.isEmpty()) {
            logger.warn("No nodes available for routing");
            return "NO_AVAILABLE_NODES";
        }

        // ✅ 3. Apply strategy
        String selectedNode = strategy.selectNode(allMetrics);

        // ✅ Logging for debugging & observability
        logger.info("Routing decision: {}", selectedNode);

        return selectedNode;
    }
}