package com.capstone.alb.service;

import com.capstone.alb.model.SystemMetrics;
import com.capstone.alb.strategy.LoadBalancingStrategy;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class RoutingService {

    private static final Logger logger = LoggerFactory.getLogger(RoutingService.class);

    private final LoadBalancingStrategy strategy;
    private final RemoteMetricsService remoteMetricsService;

    public RoutingService(
            LoadBalancingStrategy strategy,
            RemoteMetricsService remoteMetricsService
    ) {
        this.strategy = strategy;
        this.remoteMetricsService = remoteMetricsService;
    }

    public String routeRequest() {
        Map<String, SystemMetrics> allMetrics = new HashMap<>();

        try {
            SystemMetrics localMetrics = remoteMetricsService.getLocalMetrics();
            if (localMetrics != null) {
                allMetrics.put("LOCAL", localMetrics);
            }

            Map<String, SystemMetrics> remoteMetrics = remoteMetricsService.fetchAllMetrics();
            if (remoteMetrics != null && !remoteMetrics.isEmpty()) {
                allMetrics.putAll(remoteMetrics);
            }
        } catch (Exception exception) {
            logger.error("Error fetching metrics", exception);
        }

        if (allMetrics.isEmpty()) {
            logger.warn("No nodes available for routing");
            return "NO_AVAILABLE_NODES";
        }

        String selectedNode = strategy.selectNode(allMetrics);
        logger.info("Routing decision: {}", selectedNode);
        return selectedNode;
    }
}
