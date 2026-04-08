package com.capstone.alb.controller;

import com.capstone.alb.service.RequestCounterService;
import com.capstone.alb.service.RequestInsightService;
import com.capstone.alb.service.RoutingService;
import com.capstone.alb.model.DashboardSnapshot;
import com.capstone.alb.model.RouteDecisionResponse;
import com.capstone.alb.model.TrafficRequest;
import jakarta.validation.Valid;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
@CrossOrigin(origins = "*")
public class LoadBalancerController {
	private final RoutingService routingService;
	private final RequestCounterService requestCounter;
    private final RequestInsightService requestInsightService;

    public LoadBalancerController(
            RoutingService routingService,
            RequestCounterService requestCounter,
            RequestInsightService requestInsightService
    ) {
        this.routingService = routingService;
        this.requestCounter = requestCounter;
        this.requestInsightService = requestInsightService;
    }

    @GetMapping("/route")
    public ResponseEntity<RouteDecisionResponse> route(HttpServletRequest servletRequest) {
        requestCounter.increment();
        TrafficRequest request = buildTrafficRequest(servletRequest, Map.of());
        return ResponseEntity.ok(routingService.routeRequest(request, requestCounter.getCount()));
    }

    @PostMapping("/route")
    public ResponseEntity<RouteDecisionResponse> route(
            HttpServletRequest servletRequest,
            @Valid @RequestBody(required = false) Map<String, Object> requestBody
    ) {
        requestCounter.increment();
        TrafficRequest request = buildTrafficRequest(servletRequest, requestBody == null ? Map.of() : requestBody);
        return ResponseEntity.ok(routingService.routeRequest(request, requestCounter.getCount()));
    }

    @GetMapping("/dashboard/snapshot")
    public ResponseEntity<DashboardSnapshot> dashboardSnapshot() {
        return ResponseEntity.ok(routingService.getDashboardSnapshot(requestCounter.getCount()));
    }

    private TrafficRequest buildTrafficRequest(HttpServletRequest servletRequest, Map<String, Object> body) {
        String sourceIp = extractSourceIp(servletRequest);
        double requestRate = requestInsightService.markAndGetRate(sourceIp);

        return new TrafficRequest(
                getDouble(body, "request_rate", requestRate),
                getInteger(body, "payload_size", (int) Math.max(servletRequest.getContentLengthLong(), 0L)),
                getString(body, "user_agent", servletRequest.getHeader("User-Agent")),
                getDouble(body, "timestamp", System.currentTimeMillis() / 1000.0),
                getInteger(body, "pkt_count", null),
                getInteger(body, "total_bytes", null),
                getInteger(body, "syn_flag_count", null),
                getInteger(body, "total_flags", null),
                getDouble(body, "header_entropy", null),
                getInteger(body, "pkt_size_max", null),
                getInteger(body, "pkt_size_min", null),
                getInteger(body, "dest_port", servletRequest.getServerPort()),
                getInteger(body, "ttl", null),
                getBoolean(body, "ip_fragmented", false),
                getInteger(body, "ipv4_ihl", null),
                getString(body, "protocol", "TCP"),
                getString(body, "method", servletRequest.getMethod()),
                getString(body, "path", servletRequest.getRequestURI()),
                getString(body, "source_ip", sourceIp)
        );
    }

    private String extractSourceIp(HttpServletRequest request) {
        String forwardedFor = request.getHeader("X-Forwarded-For");
        if (forwardedFor != null && !forwardedFor.isBlank()) {
            return forwardedFor.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }

    private static String getString(Map<String, Object> body, String key, String defaultValue) {
        Object value = body.get(key);
        return value != null ? String.valueOf(value) : defaultValue;
    }

    private static Integer getInteger(Map<String, Object> body, String key, Integer defaultValue) {
        Object value = body.get(key);
        if (value == null) {
            return defaultValue;
        }
        if (value instanceof Number number) {
            return number.intValue();
        }
        return Integer.parseInt(String.valueOf(value));
    }

    private static Double getDouble(Map<String, Object> body, String key, Double defaultValue) {
        Object value = body.get(key);
        if (value == null) {
            return defaultValue;
        }
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        return Double.parseDouble(String.valueOf(value));
    }

    private static Boolean getBoolean(Map<String, Object> body, String key, Boolean defaultValue) {
        Object value = body.get(key);
        if (value == null) {
            return defaultValue;
        }
        if (value instanceof Boolean bool) {
            return bool;
        }
        return Boolean.parseBoolean(String.valueOf(value));
    }
}
