package com.capstone.alb.controller;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.net.InetAddress;
import java.time.Instant;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import com.capstone.alb.model.SystemMetrics;
import com.capstone.alb.service.RequestCounterService;
import com.sun.management.OperatingSystemMXBean;

@RestController
public class MetricsController {

    private final RequestCounterService requestCounter;

    public MetricsController(RequestCounterService requestCounter) {
        this.requestCounter = requestCounter;
    }

    @GetMapping("/metrics")
    public SystemMetrics getMetrics() {

        OperatingSystemMXBean osBean =
                ManagementFactory.getPlatformMXBean(OperatingSystemMXBean.class);

        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();

        double cpuUsage = safePercentage(osBean.getCpuLoad());
        double processCpuLoad = safePercentage(osBean.getProcessCpuLoad());

        int cpuCores = osBean.getAvailableProcessors();

        long totalMemory = osBean.getTotalMemorySize();
        long freeMemory = osBean.getFreeMemorySize();

        double memoryUsage = totalMemory > 0
                ? ((double) (totalMemory - freeMemory) / totalMemory) * 100
                : 0;

        long heapUsed = memoryBean.getHeapMemoryUsage().getUsed();

        String hostname = getHostnameSafe();
        String serverId = hostname;

        return new SystemMetrics(
                serverId,
                hostname,
                cpuUsage,
                processCpuLoad,
                cpuCores,
                memoryUsage,
                heapUsed,
                requestCounter.getCount(),
                Instant.now()
        );
    }

    // ✅ Prevents -1 or invalid CPU values
    private double safePercentage(double value) {
        if (value < 0) return 0;
        return value * 100;
    }

    // ✅ Prevents crash if hostname fails
    private String getHostnameSafe() {
        try {
            return InetAddress.getLocalHost().getHostName();
        } catch (Exception e) {
            return "unknown-host";
        }
    }
}