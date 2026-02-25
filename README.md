# AI-Driven Load Balancer with Automated Anomaly Detection

## Project Overview
This repository contains a resilient, distributed Layer 7 Load Balancer developed in Java. The system is integrated with a Python-based AI Security Sentinel that utilizes the Isolation Forest machine learning algorithm to detect and mitigate malicious traffic in real-time. System analytics and health metrics are visualized through a React-based Monitoring Dashboard.

## Repository Structure
* **alb-core-service**: Core Java engine implementing Strategy, Chain of Responsibility, and Observer design patterns for request routing and system events.
* **security-sentinel-api**: Python FastAPI microservice responsible for real-time traffic feature extraction and anomaly detection.
* **monitoring-dashboard-ui**: React and Tailwind CSS frontend providing visualization of traffic logs, threat levels, and system throughput.
* **infrastructure**: Configuration files for environment orchestration, including Docker and network tunneling utilities.
* **docs**: Technical documentation, including system architecture diagrams and API specifications.

## Technical Stack
* **Backend**: Java 17, Maven
* **AI/Security**: Python 3.9+, FastAPI, Scikit-Learn
* **Frontend**: React.js, Tailwind CSS
* **Database**: MongoDB Atlas (Centralized Logging and Threat Intelligence)

## Branching Strategy
* **master**: Contains stable, production-ready code. All releases are tagged from this branch.
* **dev**: Primary integration branch for active development and feature testing.
* **feature/ALB-X**: Individual branches dedicated to specific Jira tasks. Feature branches must be merged into dev via Pull Request.
