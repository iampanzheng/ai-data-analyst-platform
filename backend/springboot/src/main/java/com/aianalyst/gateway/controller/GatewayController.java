package com.aianalyst.gateway.controller;

import com.aianalyst.gateway.dto.QueryRequest;
import com.aianalyst.gateway.service.FastApiClient;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

import com.aianalyst.gateway.service.FastApiClient.FastApiProxyException;

@RestController
@RequestMapping("/api")
public class GatewayController {
    private final FastApiClient fastApiClient;

    public GatewayController(FastApiClient fastApiClient) {
        this.fastApiClient = fastApiClient;
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok(fastApiClient.health());
    }

    @GetMapping("/schema")
    public ResponseEntity<String> schema() {
        return ResponseEntity.ok(fastApiClient.schema());
    }

    @PostMapping("/query")
    public ResponseEntity<String> query(
            @Valid @RequestBody QueryRequest request,
            @RequestHeader(value = "X-Trace-ID", required = false) String traceId) {
        String effectiveTraceId = traceId == null || traceId.isBlank() ? UUID.randomUUID().toString() : traceId;
        return ResponseEntity.ok(fastApiClient.query(request.sql(), effectiveTraceId));
    }
}


@org.springframework.web.bind.annotation.RestControllerAdvice
class GatewayExceptionHandler {
    @org.springframework.web.bind.annotation.ExceptionHandler(FastApiProxyException.class)
    ResponseEntity<String> handleFastApi(FastApiProxyException ex) {
        return ResponseEntity.status(HttpStatus.valueOf(ex.status())).body(ex.responseBody());
    }
}
