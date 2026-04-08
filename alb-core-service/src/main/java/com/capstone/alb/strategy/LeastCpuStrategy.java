package com.capstone.alb.strategy;

import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;
import com.capstone.alb.model.SystemMetrics;

@Component
@Primary
public class LeastCpuStrategy implements LoadBalancingStrategy {

    private static final Logger logger = LoggerFactory.getLogger(LeastCpuStrategy.class);

    @Override
    public String selectNode(Map<String, SystemMetrics> metrics) {

        double lowestCpu = Double.MAX_VALUE;
        String bestNode = null;

        for (Map.Entry<String, SystemMetrics> entry : metrics.entrySet()) {

            String node = entry.getKey();
            SystemMetrics data = entry.getValue();

            if (data == null) continue;

            double cpu = data.getCpuUsage();

            logger.debug("Node: {} | CPU: {}", node, cpu);

            if (cpu < lowestCpu) {
                lowestCpu = cpu;
                bestNode = node;
            }
        }

        if (bestNode == null) {
            logger.warn("No suitable node found, defaulting fallback");
            return "NO_NODE_AVAILABLE";
        }

        logger.info("Selected node (Least CPU): {} with CPU: {}", bestNode, lowestCpu);

        return bestNode;
    }
}