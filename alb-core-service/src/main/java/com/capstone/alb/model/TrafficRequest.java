package com.capstone.alb.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.PositiveOrZero;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

public record TrafficRequest(
        @JsonProperty("request_rate")
        @PositiveOrZero(message = "request_rate must be non-negative")
        Double requestRate,

        @JsonProperty("payload_size")
        @PositiveOrZero(message = "payload_size must be non-negative")
        Integer payloadSize,

        @JsonProperty("user_agent")
        String userAgent,

        Double timestamp,

        @JsonProperty("pkt_count")
        @PositiveOrZero(message = "pkt_count must be non-negative")
        Integer pktCount,

        @JsonProperty("total_bytes")
        @PositiveOrZero(message = "total_bytes must be non-negative")
        Integer totalBytes,

        @JsonProperty("syn_flag_count")
        @PositiveOrZero(message = "syn_flag_count must be non-negative")
        Integer synFlagCount,

        @JsonProperty("total_flags")
        @PositiveOrZero(message = "total_flags must be non-negative")
        Integer totalFlags,

        @JsonProperty("header_entropy")
        @PositiveOrZero(message = "header_entropy must be non-negative")
        Double headerEntropy,

        @JsonProperty("pkt_size_max")
        @PositiveOrZero(message = "pkt_size_max must be non-negative")
        Integer pktSizeMax,

        @JsonProperty("pkt_size_min")
        @PositiveOrZero(message = "pkt_size_min must be non-negative")
        Integer pktSizeMin,

        @JsonProperty("dest_port")
        @Min(value = 1, message = "dest_port must be at least 1")
        Integer destPort,

        @PositiveOrZero(message = "ttl must be non-negative")
        Integer ttl,

        @JsonProperty("ip_fragmented")
        Boolean ipFragmented,

        @JsonProperty("ipv4_ihl")
        @PositiveOrZero(message = "ipv4_ihl must be non-negative")
        Integer ipv4Ihl,

        String protocol,
        String method,
        String path,

        @JsonProperty("source_ip")
        String sourceIp
) {
    public static TrafficRequest empty() {
        return new TrafficRequest(
                null, null, null, null, null, null, null, null, null,
                null, null, null, null, null, null, null, null, null, null
        );
    }

    @JsonIgnore
    public String requestId() {
        return UUID.randomUUID().toString();
    }

    @JsonIgnore
    public double resolvedRequestRate() {
        return requestRate != null ? requestRate : 1.0;
    }

    @JsonIgnore
    public int resolvedPayloadSize() {
        return payloadSize != null ? payloadSize : 0;
    }

    @JsonIgnore
    public String resolvedUserAgent() {
        return userAgent != null && !userAgent.isBlank() ? userAgent : "Codex-Simulator/1.0";
    }

    @JsonIgnore
    public double resolvedTimestamp() {
        return timestamp != null ? timestamp : Instant.now().toEpochMilli() / 1000.0;
    }

    @JsonIgnore
    public int resolvedDestPort() {
        return destPort != null ? destPort : 80;
    }

    @JsonIgnore
    public int resolvedTtl() {
        return ttl != null ? ttl : 64;
    }

    @JsonIgnore
    public boolean resolvedIpFragmented() {
        return Boolean.TRUE.equals(ipFragmented);
    }

    @JsonIgnore
    public int resolvedIpv4Ihl() {
        return ipv4Ihl != null ? ipv4Ihl : 5;
    }

    @JsonIgnore
    public String resolvedProtocol() {
        return protocol != null && !protocol.isBlank() ? protocol : "TCP";
    }

    @JsonIgnore
    public String resolvedMethod() {
        return method != null && !method.isBlank() ? method : "GET";
    }

    @JsonIgnore
    public String resolvedPath() {
        return path != null && !path.isBlank() ? path : "/api/resource";
    }

    @JsonIgnore
    public String resolvedSourceIp() {
        return sourceIp != null && !sourceIp.isBlank() ? sourceIp : "192.168.10.10";
    }

    @JsonIgnore
    public Map<String, Object> toSentinelPayload() {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("request_rate", resolvedRequestRate());
        payload.put("payload_size", resolvedPayloadSize());
        payload.put("user_agent", resolvedUserAgent());
        payload.put("timestamp", resolvedTimestamp());
        payload.put("dest_port", resolvedDestPort());
        payload.put("ttl", resolvedTtl());
        payload.put("ip_fragmented", resolvedIpFragmented());
        payload.put("ipv4_ihl", resolvedIpv4Ihl());
        payload.put("protocol", resolvedProtocol());

        putIfPresent(payload, "pkt_count", pktCount);
        putIfPresent(payload, "total_bytes", totalBytes);
        putIfPresent(payload, "syn_flag_count", synFlagCount);
        putIfPresent(payload, "total_flags", totalFlags);
        putIfPresent(payload, "header_entropy", headerEntropy);
        putIfPresent(payload, "pkt_size_max", pktSizeMax);
        putIfPresent(payload, "pkt_size_min", pktSizeMin);

        return payload;
    }

    @JsonIgnore
    public Map<String, Object> toClientSummary() {
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("request_rate", resolvedRequestRate());
        summary.put("payload_size", resolvedPayloadSize());
        summary.put("user_agent", resolvedUserAgent());
        summary.put("dest_port", resolvedDestPort());
        summary.put("protocol", resolvedProtocol());
        summary.put("method", resolvedMethod());
        summary.put("path", resolvedPath());
        summary.put("source_ip", resolvedSourceIp());
        summary.put("ttl", resolvedTtl());
        summary.put("ip_fragmented", resolvedIpFragmented());
        return summary;
    }

    private static void putIfPresent(Map<String, Object> payload, String key, Object value) {
        if (value != null) {
            payload.put(key, value);
        }
    }
}
