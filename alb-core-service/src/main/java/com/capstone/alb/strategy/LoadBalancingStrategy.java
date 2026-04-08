package com.capstone.alb.strategy;

import java.util.Map;
import com.capstone.alb.model.SystemMetrics;

public interface LoadBalancingStrategy {

    String selectNode(Map<String, SystemMetrics> metrics);
}