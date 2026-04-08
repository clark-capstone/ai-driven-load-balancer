package com.capstone.alb.service;

import com.capstone.alb.model.SystemMetrics;
import com.capstone.alb.model.ThreatScoreResponse;
import com.capstone.alb.model.TrafficRequest;
import com.capstone.alb.strategy.LoadBalancingStrategy;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

@Service
public class RoutingService {

    private static final Logger logger = LoggerFactory.getLogger(RoutingService.class);

    private final LoadBalancingStrategy strategy;
    private final RemoteMetricsService remoteMetricsService;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${sentinel.api.base-url:http://localhost:8000}")
    private String sentinelBaseUrl;

    public RoutingService(
            LoadBalancingStrategy strategy,
            RemoteMetricsService remoteMetricsService
    ) {
        this.strategy = strategy;
        this.remoteMetricsService = remoteMetricsService;
    }

    public String routeRequest(TrafficRequest request) {
        ThreatScoreResponse threatScore = scoreTraffic(request);
        if ("block".equalsIgnoreCase(threatScore.result())) {
            logger.warn(
                    "Request blocked by AI Sentinel | confidence={} | metadata={}",
                    threatScore.confidence(),
                    threatScore.metadata()
            );
            return "BLOCKED_BY_AI_SENTINEL";
        }

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

    private ThreatScoreResponse scoreTraffic(TrafficRequest request) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        try {
            ThreatScoreResponse response = restTemplate.postForObject(
                    sentinelBaseUrl + "/score",
                    new HttpEntity<>(request.toSentinelPayload(), headers),
                    ThreatScoreResponse.class
            );
            if (response != null) {
                return response;
            }
        } catch (RestClientException exception) {
            logger.warn("Sentinel scoring unavailable, defaulting to allow", exception);
        }

        return new ThreatScoreResponse(
                "allow",
                0.0,
                "sentinel-unavailable",
                0.0,
                Map.of("fallback", true)
        );
    }
}
