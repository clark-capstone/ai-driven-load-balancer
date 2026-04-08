package com.capstone.alb.controller;

import java.lang.management.ManagementFactory;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import com.sun.management.OperatingSystemMXBean;

@RestController
@CrossOrigin(origins = "*")
public class CpuController {

	@GetMapping("/cpu")
    public double cpu() {

        OperatingSystemMXBean osBean = ManagementFactory.getPlatformMXBean(OperatingSystemMXBean.class);
        double cpuLoad = osBean.getCpuLoad() * 100;
        return cpuLoad;
    }
}
