package com.capstone.alb.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import com.capstone.alb.service.RequestCounterService;
import com.capstone.alb.service.RoutingService;

@RestController
public class LoadBalancerController {
	private final RoutingService routingService;
	private final RequestCounterService requestCounter;

    public LoadBalancerController(RoutingService routingService, RequestCounterService requestCounter) {
        this.routingService = routingService;
        this.requestCounter = requestCounter;
    }

    @GetMapping("/route")
    public ResponseEntity<String> route() {
        requestCounter.increment();
        return routingService.routeRequest();
    }
}
