package com.capstone.alb.service;

import java.util.concurrent.atomic.AtomicLong;
import org.springframework.stereotype.Service;

@Service
public class RequestCounterService {

	private final AtomicLong requestCount = new AtomicLong();

    public void increment() {
        requestCount.incrementAndGet();
    }

    public long getCount() {
        return requestCount.get();
    }
}
