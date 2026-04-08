package com.capstone.alb.service;

import com.capstone.alb.model.RouteDecisionResponse;
import com.capstone.alb.model.DashboardSnapshot;
import com.capstone.alb.model.RouteLogEntry;
import com.capstone.alb.model.ThreatScoreResponse;
import com.capstone.alb.model.TrafficRequest;
import com.capstone.alb.strategy.LoadBalancingStrategy;
import java.time.OffsetDateTime;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

@Service
public class RoutingService {

    private final LoadBalancingStrategy strategy;
    private final RouteEventStore routeEventStore;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${sentinel.api.base-url:http://localhost:8000}")
    private String sentinelBaseUrl;

    @Value("${sentinel.collection.bad-confidence-threshold:0.75}")
    private double badConfidenceThreshold;

    @Value("${sentinel.collection.review-confidence-threshold:0.45}")
    private double reviewConfidenceThreshold;

    public RoutingService(LoadBalancingStrategy strategy, RouteEventStore routeEventStore) {
        this.strategy = strategy;
        this.routeEventStore = routeEventStore;
    }

    public RouteDecisionResponse routeRequest(TrafficRequest request, long totalRequests) {
        String requestId = request.requestId();
        ThreatScoreResponse threatScore = applyLocalGuards(request, scoreTraffic(request));
        boolean blocked = "block".equalsIgnoreCase(threatScore.result());

        String selectedServer = blocked ? null : strategy.getNextServer();
        String serverName = selectedServer == null ? "Sentinel" : "Server-" + selectedServer;
        String confidenceBand = resolveConfidenceBand(threatScore.confidence());
        String collection = resolveCollection(threatScore, blocked);
        String responseMessage = blocked
                ? "Blocked by AI Security Sentinel"
                : "Handled by Service " + selectedServer;

        Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("model_version", threatScore.modelVersion());
        metadata.put("inference_ms", threatScore.inferenceMs());
        metadata.put("sentinel_metadata", threatScore.metadata());

        RouteLogEntry log = new RouteLogEntry(
                requestId,
                OffsetDateTime.now().toString(),
                blocked ? "BLOCKED" : "ALLOWED",
                collection,
                confidenceBand,
                threatScore.confidence(),
                selectedServer,
                serverName,
                responseMessage,
                buildReason(blocked, threatScore),
                request.resolvedSourceIp(),
                request.toClientSummary(),
                metadata
        );

        RouteDecisionResponse response = new RouteDecisionResponse(
                requestId,
                threatScore.result(),
                collection,
                confidenceBand,
                threatScore.confidence(),
                selectedServer,
                serverName,
                totalRequests,
                responseMessage,
                log
        );
        routeEventStore.append(log);
        return response;
    }

    public DashboardSnapshot getDashboardSnapshot(long totalRequests) {
        return routeEventStore.snapshot(totalRequests);
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
            if (response == null) {
                return fallbackThreatScore(request, "Sentinel returned an empty response");
            }
            return response;
        } catch (RestClientException ex) {
            return fallbackThreatScore(request, ex.getMessage());
        }
    }

    private ThreatScoreResponse fallbackThreatScore(TrafficRequest request, String reason) {
        boolean payloadLooksSuspicious =
                request.resolvedPayloadSize() > 0 && request.resolvedPayloadSize() <= 64;
        boolean suspicious =
                request.resolvedRequestRate() >= 120.0
                        || (payloadLooksSuspicious && request.resolvedRequestRate() >= 60.0)
                        || request.resolvedIpFragmented();

        double confidence = suspicious ? 0.82 : 0.18;
        Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("fallback", true);
        metadata.put("reason", reason);
        metadata.put("rule", suspicious ? "local_traffic_heuristic" : "local_default_allow");

        return new ThreatScoreResponse(
                suspicious ? "block" : "allow",
                confidence,
                "fallback-local",
                0.0,
                metadata
        );
    }

    private ThreatScoreResponse applyLocalGuards(TrafficRequest request, ThreatScoreResponse threatScore) {
        boolean burstRule = request.resolvedRequestRate() >= 10.0 && request.resolvedPayloadSize() <= 256;
        if (!burstRule || "block".equalsIgnoreCase(threatScore.result())) {
            return threatScore;
        }

        Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("upstream_result", threatScore.result());
        metadata.put("upstream_confidence", threatScore.confidence());
        metadata.put("local_guard", "burst_rate_small_payload");
        metadata.put("request_rate", request.resolvedRequestRate());
        metadata.put("payload_size", request.resolvedPayloadSize());

        return new ThreatScoreResponse(
                "block",
                Math.max(threatScore.confidence(), 0.91),
                threatScore.modelVersion(),
                threatScore.inferenceMs(),
                metadata
        );
    }

    private String resolveCollection(ThreatScoreResponse threatScore, boolean blocked) {
        if (blocked || threatScore.confidence() >= badConfidenceThreshold) {
            return "bad-calls";
        }
        if (threatScore.confidence() >= reviewConfidenceThreshold) {
            return "needs-review";
        }
        return "normal";
    }

    private String resolveConfidenceBand(double confidence) {
        if (confidence >= badConfidenceThreshold) {
            return "high";
        }
        if (confidence >= reviewConfidenceThreshold) {
            return "medium";
        }
        return "low";
    }

    private String buildReason(boolean blocked, ThreatScoreResponse threatScore) {
        if (blocked) {
            return "Threat detection flagged this request for manual review";
        }
        if ("high".equals(resolveConfidenceBand(threatScore.confidence()))) {
            return "Allowed, but confidence is elevated enough to keep in bad-calls";
        }
        if ("medium".equals(resolveConfidenceBand(threatScore.confidence()))) {
            return "Allowed with moderate confidence, added to review collection";
        }
        return "Allowed as normal traffic";
    }
}
