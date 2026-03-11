package com.capstone.alb.controller;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.net.InetAddress;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
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
    public SystemMetrics getMetrics() throws Exception {

        OperatingSystemMXBean osBean =
                ManagementFactory.getPlatformMXBean(OperatingSystemMXBean.class);

        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();

        double cpuUsage = osBean.getCpuLoad() * 100;
        double processCpuLoad = osBean.getProcessCpuLoad() * 100;

        int cpuCores = osBean.getAvailableProcessors();

        long totalMemory = osBean.getTotalMemorySize();
        long freeMemory = osBean.getFreeMemorySize();

        double memoryUsage =
                ((double)(totalMemory - freeMemory) / totalMemory) * 100;

        long heapUsed = memoryBean.getHeapMemoryUsage().getUsed();

        String hostname = InetAddress.getLocalHost().getHostName();

        String serverId = hostname;

        String timestamp =
                LocalDateTime.now()
                        .format(DateTimeFormatter.ofPattern("MM-dd-yyyy HH:mm:ss"));

        return new SystemMetrics(
                serverId,
                hostname,
                cpuUsage,
                processCpuLoad,
                cpuCores,
                memoryUsage,
                heapUsed,
                requestCounter.getCount(),
                timestamp
        );
    }
}