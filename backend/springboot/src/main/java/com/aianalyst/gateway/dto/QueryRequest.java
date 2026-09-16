package com.aianalyst.gateway.dto;

import jakarta.validation.constraints.NotBlank;

public record QueryRequest(
        @NotBlank(message = "sql must not be blank")
        String sql
) {}
