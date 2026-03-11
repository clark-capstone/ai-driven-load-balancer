package com.capstone.alb.metrics;

import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.stereotype.Service;

@Service
public class TrafficMetricsService {

	private final AtomicInteger totalRequests = new AtomicInteger(0);

    public void incrementRequests() {
        totalRequests.incrementAndGet();
    }

    public int getTotalRequests() {
        return totalRequests.get();
    }
}
