package com.capstone.alb.service;

import java.util.concurrent.atomic.AtomicLong;

import org.springframework.stereotype.Service;

@Service
public class RequestCounterService {

    // ✅ Total requests handled by this node
    private final AtomicLong requestCount = new AtomicLong(0);

    // ✅ Increment request count
    public void increment() {
        requestCount.incrementAndGet();
    }

    // ✅ Get total request count
    public long getCount() {
        return requestCount.get();
    }

    // ✅ Reset counter (useful for testing / sliding window metrics later)
    public void reset() {
        requestCount.set(0);
    }
}