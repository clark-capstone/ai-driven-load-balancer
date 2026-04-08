package com.capstone.alb.service;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Service;

@Service
public class RequestInsightService {

    private static final Duration WINDOW = Duration.ofSeconds(5);
    private final Map<String, Deque<Instant>> requestsPerIp = new ConcurrentHashMap<>();

    public double markAndGetRate(String sourceIp) {
        Instant now = Instant.now();
        Deque<Instant> timestamps = requestsPerIp.computeIfAbsent(sourceIp, key -> new ArrayDeque<>());

        synchronized (timestamps) {
            timestamps.addLast(now);
            trimOldEntries(timestamps, now);
            if (timestamps.size() <= 1) {
                return 1.0;
            }

            Instant first = timestamps.peekFirst();
            double elapsedSeconds = Math.max(
                    Duration.between(first, now).toMillis() / 1000.0,
                    1.0
            );
            return timestamps.size() / elapsedSeconds;
        }
    }

    private void trimOldEntries(Deque<Instant> timestamps, Instant now) {
        Instant cutoff = now.minus(WINDOW);
        while (!timestamps.isEmpty() && timestamps.peekFirst().isBefore(cutoff)) {
            timestamps.pollFirst();
        }
    }
}
