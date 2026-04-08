package com.capstone.alb.service;

import com.capstone.alb.model.DashboardSnapshot;
import com.capstone.alb.model.RouteLogEntry;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentLinkedDeque;
import org.springframework.stereotype.Service;

@Service
public class RouteEventStore {

    private static final int MAX_EVENTS = 300;
    private final ConcurrentLinkedDeque<RouteLogEntry> logs = new ConcurrentLinkedDeque<>();

    public void append(RouteLogEntry log) {
        logs.addFirst(log);
        while (logs.size() > MAX_EVENTS) {
            logs.pollLast();
        }
    }

    public DashboardSnapshot snapshot(long totalRequests) {
        List<RouteLogEntry> entries = logs.stream().toList();

        Map<String, Integer> collectionCounts = new LinkedHashMap<>();
        collectionCounts.put("all", entries.size());
        collectionCounts.put("normal", 0);
        collectionCounts.put("needs-review", 0);
        collectionCounts.put("bad-calls", 0);

        Map<String, Integer> serverRequestCounts = new LinkedHashMap<>();
        serverRequestCounts.put("A", 0);
        serverRequestCounts.put("B", 0);
        serverRequestCounts.put("C", 0);

        Map<String, Integer> blockedPerServer = new LinkedHashMap<>();
        blockedPerServer.put("A", 0);
        blockedPerServer.put("B", 0);
        blockedPerServer.put("C", 0);

        for (RouteLogEntry entry : entries) {
            collectionCounts.computeIfPresent(entry.collection(), (key, value) -> value + 1);
            if (entry.serverId() != null) {
                serverRequestCounts.computeIfPresent(entry.serverId(), (key, value) -> value + 1);
                if ("BLOCKED".equals(entry.status())) {
                    blockedPerServer.computeIfPresent(entry.serverId(), (key, value) -> value + 1);
                }
            }
        }

        List<RouteLogEntry> orderedLogs = new ArrayList<>(entries);
        orderedLogs.sort(Comparator.comparing(RouteLogEntry::timestamp).reversed());

        return new DashboardSnapshot(
                totalRequests,
                collectionCounts,
                serverRequestCounts,
                blockedPerServer,
                orderedLogs
        );
    }
}
