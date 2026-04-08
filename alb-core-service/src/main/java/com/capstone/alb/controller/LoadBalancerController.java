package com.capstone.alb.controller;

import com.capstone.alb.service.RequestCounterService;
import com.capstone.alb.service.RoutingService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@CrossOrigin(origins = "*")
public class LoadBalancerController {

    private final RoutingService routingService;
    private final RequestCounterService requestCounter;

    public LoadBalancerController(
            RoutingService routingService,
            RequestCounterService requestCounter
    ) {
        this.routingService = routingService;
        this.requestCounter = requestCounter;
    }

    @GetMapping("/route")
    public ResponseEntity<String> route() {
        return routeRequest();
    }

    @PostMapping("/route")
    public ResponseEntity<String> routePost() {
        return routeRequest();
    }

    private ResponseEntity<String> routeRequest() {
        requestCounter.increment();
        String selectedNode = routingService.routeRequest();
        return ResponseEntity.ok("Request routed to: " + selectedNode);
    }
}
