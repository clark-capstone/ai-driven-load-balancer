package com.capstone.alb.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class TestController {

	@GetMapping("/api/testA")
    public String testA() {
        return "Handled by Service A";
    }

    @GetMapping("/api/testB")
    public String testB() {
        return "Handled by Service B";
    }
}
