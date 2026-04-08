package com.capstone.alb.metrics;

import java.util.concurrent.atomic.AtomicLong;

import org.springframework.stereotype.Service;

@Service
public class TrafficMetricsService {

    // ✅ Total requests handled by this node
    private final AtomicLong totalRequests = new AtomicLong(0);

    // ✅ Increment request count
    public void incrementRequests() {
        totalRequests.incrementAndGet();
    }

    // ✅ Get total requests
    public long getTotalRequests() {
        return totalRequests.get();
    }

    // ✅ Reset (useful for testing or future sliding window logic)
    public void reset() {
        totalRequests.set(0);
    }
}