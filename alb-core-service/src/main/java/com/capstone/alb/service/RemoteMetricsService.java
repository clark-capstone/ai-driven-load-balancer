package com.capstone.alb.service;

import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import com.capstone.alb.config.NodeRegistry;
import com.capstone.alb.controller.MetricsController;
import com.capstone.alb.model.SystemMetrics;

@Service
public class RemoteMetricsService {

    private static final Logger logger = LoggerFactory.getLogger(RemoteMetricsService.class);

    private final RestTemplate restTemplate;
    private final NodeRegistry nodeRegistry;
    private final MetricsController metricsController;

    public RemoteMetricsService(NodeRegistry nodeRegistry,
                                MetricsController metricsController) {
        this.nodeRegistry = nodeRegistry;
        this.metricsController = metricsController;
        this.restTemplate = new RestTemplate();
    }

    // ✅ Fetch metrics from all remote nodes
    public Map<String, SystemMetrics> fetchAllMetrics() {

        Map<String, SystemMetrics> metricsMap = new HashMap<>();

        for (String node : nodeRegistry.getNodes()) {
            try {
                String url = node + "/metrics";

                SystemMetrics metrics =
                        restTemplate.getForObject(url, SystemMetrics.class);

                if (metrics != null) {
                    metricsMap.put(node, metrics);
                    logger.info("Fetched metrics from {}", node);
                }

            } catch (Exception e) {
                logger.warn("Failed to fetch metrics from {} | Skipping...", node);
            }
        }

        return metricsMap;
    }

    // ✅ Get local node metrics (no HTTP call)
    public SystemMetrics getLocalMetrics() {
        try {
            return metricsController.getMetrics();
        } catch (Exception e) {
            logger.error("Failed to fetch local metrics", e);
            return null;
        }
    }
}