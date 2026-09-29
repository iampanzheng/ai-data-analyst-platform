package com.aianalyst.gateway.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;

@Service
public class FastApiClient {
    private final HttpClient httpClient;
    private final String baseUrl;

    public FastApiClient(
            @Value("${app.fastapi.base-url:http://fastapi:8000}") String baseUrl) {
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(5))
                .build();
        this.baseUrl = trimTrailingSlash(baseUrl);
    }

    public String health() {
        return send("GET", "/health", null, null);
    }

    public String schema() {
        return send("GET", "/api/schema", null, null);
    }

    public String query(String sql, String traceId) {
        return send("POST", "/api/query", toJsonSql(sql), traceId);
    }

    public String analyze(String question, String routingMode, String traceId) {
        return send("POST", "/api/analyze", toJsonAnalyze(question, routingMode), traceId);
    }

    private String send(String method, String path, String body, String traceId) {
        try {
            HttpRequest.Builder requestBuilder = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + path))
                    .header("Accept", "application/json");

            if (traceId != null && !traceId.isBlank()) {
                requestBuilder.header("X-Trace-ID", traceId);
            }

            if (body != null) {
                requestBuilder
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8));
            } else {
                requestBuilder.method(method, HttpRequest.BodyPublishers.noBody());
            }

            HttpRequest request = requestBuilder.build();
            logOutbound(request, body);

            HttpResponse<String> response = httpClient.send(
                    request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));

            logInbound(response);

            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                throw new FastApiProxyException(response.statusCode(), response.body());
            }
            return response.body();
        } catch (FastApiProxyException ex) {
            throw ex;
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new FastApiProxyException(503, "FastAPI request interrupted");
        } catch (IOException | IllegalArgumentException ex) {
            throw new FastApiProxyException(503, "FastAPI request failed: " + ex.getMessage());
        }
    }

    private void logOutbound(HttpRequest request, String body) {
        byte[] bodyBytes = body == null ? new byte[0] : body.getBytes(StandardCharsets.UTF_8);
        System.out.println("[FASTAPI_OUTBOUND] method=" + request.method()
                + " httpVersion=" + httpClient.version()
                + " uri=" + request.uri()
                + " contentType=" + request.headers().firstValue("Content-Type").orElse(null)
                + " contentLength=" + bodyBytes.length
                + " bodyLength=" + bodyBytes.length
                + " body=" + (body == null ? "" : body));
    }

    private static void logInbound(HttpResponse<String> response) {
        String responseBody = response.body() == null ? "" : response.body();
        System.out.println("[FASTAPI_INBOUND] status=" + response.statusCode()
                + " contentType=" + response.headers().firstValue("Content-Type").orElse(null)
                + " contentLength=" + responseBody.getBytes(StandardCharsets.UTF_8).length
                + " body=" + responseBody);
    }

    private static String trimTrailingSlash(String url) {
        return url.endsWith("/") ? url.substring(0, url.length() - 1) : url;
    }

    private static String toJsonSql(String sql) {
        return "{\"sql\":\"" + escapeJson(sql) + "\"}";
    }

    private static String toJsonAnalyze(String question, String routingMode) {
        return "{\"question\":\"" + escapeJson(question)
                + "\",\"routing_mode\":\"" + escapeJson(routingMode) + "\"}";
    }

    private static String escapeJson(String value) {
        StringBuilder result = new StringBuilder(value.length() + 16);
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"' -> result.append("\\\"");
                case '\\' -> result.append("\\\\");
                case '\b' -> result.append("\\b");
                case '\f' -> result.append("\\f");
                case '\n' -> result.append("\\n");
                case '\r' -> result.append("\\r");
                case '\t' -> result.append("\\t");
                default -> {
                    if (c < 0x20) result.append(String.format("\\u%04x", (int) c));
                    else result.append(c);
                }
            }
        }
        return result.toString();
    }

    public static final class FastApiProxyException extends RuntimeException {
        private final int status;
        private final String responseBody;

        public FastApiProxyException(int status, String responseBody) {
            super("FastAPI request failed: " + status);
            this.status = status;
            this.responseBody = responseBody;
        }

        public int status() { return status; }
        public String responseBody() { return responseBody; }
    }
}
