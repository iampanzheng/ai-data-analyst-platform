package com.aianalyst.gateway.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record AnalyzeRequest(
        @NotBlank @Size(max = 2000) String question,
        @Pattern(regexp = "auto|remote|local") String routingMode
) {
    public String effectiveRoutingMode() {
        return routingMode == null || routingMode.isBlank() ? "auto" : routingMode;
    }
}
