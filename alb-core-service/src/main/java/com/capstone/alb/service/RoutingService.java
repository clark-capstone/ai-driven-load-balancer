package com.capstone.alb.service;

import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import com.capstone.alb.metrics.TrafficMetricsService;
import com.capstone.alb.strategy.LoadBalancingStrategy;
import com.sun.management.OperatingSystemMXBean;
import java.lang.management.ManagementFactory;

@Service
public class RoutingService {
	
	private final LoadBalancingStrategy strategy;

    public RoutingService(LoadBalancingStrategy strategy) {
        this.strategy = strategy;
    }

    public ResponseEntity<String> routeRequest() {

        OperatingSystemMXBean osBean =
                ManagementFactory.getPlatformMXBean(OperatingSystemMXBean.class);

        double cpuUsage = osBean.getCpuLoad() * 100;
        System.out.println("CPU Usage: " + cpuUsage);
        if (cpuUsage < 50) {
            return ResponseEntity.ok("Handled by Service A");
        } else {
            return ResponseEntity.ok("Handled by Service B");
        }
    }
}
