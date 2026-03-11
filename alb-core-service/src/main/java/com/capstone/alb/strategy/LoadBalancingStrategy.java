package com.capstone.alb.strategy;

public interface LoadBalancingStrategy {
	String getNextServer();
}
