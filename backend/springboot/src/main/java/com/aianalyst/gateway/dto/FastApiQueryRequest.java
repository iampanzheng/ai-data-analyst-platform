package com.aianalyst.gateway.dto;

/** Request payload sent from the Spring Boot gateway to FastAPI. */
public record FastApiQueryRequest(String sql) {}
