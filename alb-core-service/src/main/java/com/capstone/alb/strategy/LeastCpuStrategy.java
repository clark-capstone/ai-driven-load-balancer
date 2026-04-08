package com.capstone.alb.strategy;

import java.util.List;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import com.sun.management.OperatingSystemMXBean;
import java.lang.management.ManagementFactory;


@Component
@Primary
public class LeastCpuStrategy implements LoadBalancingStrategy {

	@Override
    public String getNextServer() {
        return "A";
    }

    private double getCpuUsage() {

        com.sun.management.OperatingSystemMXBean osBean =
                java.lang.management.ManagementFactory.getPlatformMXBean(
                        com.sun.management.OperatingSystemMXBean.class);

        return osBean.getCpuLoad() * 100;
    }
}
