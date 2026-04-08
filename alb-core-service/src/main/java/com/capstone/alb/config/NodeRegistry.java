package com.capstone.alb.config;

import java.util.List;
import org.springframework.stereotype.Component;

@Component
public class NodeRegistry {

    public List<String> getNodes() {
        return List.of(
                "https://a5a3-2600-6c64-623f-76f6-e955-1de0-2335-545e.ngrok-free.app"
        );
    }
}
