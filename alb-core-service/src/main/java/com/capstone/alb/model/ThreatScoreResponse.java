package com.capstone.alb.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

public record ThreatScoreResponse(
        String result,
        double confidence,
        @JsonProperty("model_version") String modelVersion,
        @JsonProperty("inference_ms") double inferenceMs,
        Map<String, Object> metadata
) {
}
