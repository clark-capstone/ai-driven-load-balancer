package com.capstone.alb.model;

import java.time.Instant;

public class SystemMetrics {

    private String serverId;
    private String hostname;

    private double cpuUsage;
    private double processCpuLoad;
    private int cpuCores;

    private double memoryUsage;
    private long heapUsed;

    private long requestCount;

    private Instant timestamp;

    // ✅ Default constructor (REQUIRED for JSON deserialization)
    public SystemMetrics() {
    }

    // ✅ Parameterized constructor
    public SystemMetrics(String serverId,
                         String hostname,
                         double cpuUsage,
                         double processCpuLoad,
                         int cpuCores,
                         double memoryUsage,
                         long heapUsed,
                         long requestCount,
                         Instant timestamp) {

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

    // ✅ Getters & Setters (needed for REST + flexibility)

    public String getServerId() {
        return serverId;
    }

    public void setServerId(String serverId) {
        this.serverId = serverId;
    }

    public String getHostname() {
        return hostname;
    }

    public void setHostname(String hostname) {
        this.hostname = hostname;
    }

    public double getCpuUsage() {
        return cpuUsage;
    }

    public void setCpuUsage(double cpuUsage) {
        this.cpuUsage = cpuUsage;
    }

    public double getProcessCpuLoad() {
        return processCpuLoad;
    }

    public void setProcessCpuLoad(double processCpuLoad) {
        this.processCpuLoad = processCpuLoad;
    }

    public int getCpuCores() {
        return cpuCores;
    }

    public void setCpuCores(int cpuCores) {
        this.cpuCores = cpuCores;
    }

    public double getMemoryUsage() {
        return memoryUsage;
    }

    public void setMemoryUsage(double memoryUsage) {
        this.memoryUsage = memoryUsage;
    }

    public long getHeapUsed() {
        return heapUsed;
    }

    public void setHeapUsed(long heapUsed) {
        this.heapUsed = heapUsed;
    }

    public long getRequestCount() {
        return requestCount;
    }

    public void setRequestCount(long requestCount) {
        this.requestCount = requestCount;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }
}