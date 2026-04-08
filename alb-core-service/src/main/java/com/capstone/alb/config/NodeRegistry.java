package com.capstone.alb.config;

import java.util.List;

import org.springframework.stereotype.Component;

@Component
public class NodeRegistry {

    // ✅ Add your ngrok URLs here
    public List<String> getNodes() {
        return List.of(
            "https://abc123.ngrok-free.app",
            "https://xyz456.ngrok-free.app"
        );
    }
}