package com.capstone.alb.model;

public class SystemMetrics {

    private String serverId;
    private String hostname;

    private double cpuUsage;
    private double processCpuLoad;
    private int cpuCores;

    private double memoryUsage;
    private long heapUsed;

    private long requestCount;

    private String timestamp;

    public SystemMetrics(String serverId,
                         String hostname,
                         double cpuUsage,
                         double processCpuLoad,
                         int cpuCores,
                         double memoryUsage,
                         long heapUsed,
                         long requestCount,
                         String timestamp) {

        this.serverId = serverId;
        this.hostname = hostname;
        this.cpuUsage = cpuUsage;
        this.processCpuLoad = processCpuLoad;
        this.cpuCores = cpuCores;
        this.memoryUsage = memoryUsage;
        this.heapUsed = heapUsed;
        this.requestCount = requestCount;
        this.timestamp = timestamp;
    }

    public String getServerId() { return serverId; }

    public String getHostname() { return hostname; }

    public double getCpuUsage() { return cpuUsage; }

    public double getProcessCpuLoad() { return processCpuLoad; }

    public int getCpuCores() { return cpuCores; }

    public double getMemoryUsage() { return memoryUsage; }

    public long getHeapUsed() { return heapUsed; }

    public long getRequestCount() { return requestCount; }

    public String getTimestamp() { return timestamp; }
}