package com.aianalyst.gateway.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record AnalyzeRequest(
        @NotBlank @Size(max = 2000) String question
) {}
