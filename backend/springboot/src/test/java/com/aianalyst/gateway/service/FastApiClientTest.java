package com.aianalyst.gateway.service;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class FastApiClientTest {
    @Test
    void querySendsRealJsonBodyOverJdkHttpClient() throws Exception {
        try (TestServer server = new TestServer(200, "{\"ok\":true}")) {
            FastApiClient client = new FastApiClient(server.baseUrl());
            assertEquals("{\"ok\":true}", client.query("SELECT 1", "day4-jdk-001"));
            assertEquals("POST", server.method);
            assertEquals("application/json", server.contentType);
            assertEquals("day4-jdk-001", server.traceId);
            assertEquals("{\"sql\":\"SELECT 1\"}", server.body);
        }
    }

    @Test
    void queryEscapesJsonCharacters() throws Exception {
        try (TestServer server = new TestServer(200, "{}")) {
            FastApiClient client = new FastApiClient(server.baseUrl());
            client.query("SELECT \"name\"\nFROM city", "day4-jdk-002");
            assertEquals("{\"sql\":\"SELECT \\\"name\\\"\\nFROM city\"}", server.body);
        }
    }

    @Test
    void non2xxResponseBecomesProxyException() throws Exception {
        try (TestServer server = new TestServer(422, "{\"detail\":\"bad body\"}")) {
            FastApiClient client = new FastApiClient(server.baseUrl());
            FastApiClient.FastApiProxyException ex = org.junit.jupiter.api.Assertions.assertThrows(
                    FastApiClient.FastApiProxyException.class,
                    () -> client.query("SELECT 1", "day4-jdk-003"));
            assertEquals(422, ex.status());
            assertTrue(ex.responseBody().contains("bad body"));
        }
    }

    private static final class TestServer implements AutoCloseable {
        private final HttpServer server;
        private final int responseStatus;
        private final String responseBody;
        private String method;
        private String contentType;
        private String traceId;
        private String body;

        TestServer(int responseStatus, String responseBody) throws IOException {
            this.responseStatus = responseStatus;
            this.responseBody = responseBody;
            this.server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            this.server.createContext("/api/query", this::handle);
            this.server.start();
        }

        String baseUrl() { return "http://127.0.0.1:" + server.getAddress().getPort(); }

        private void handle(HttpExchange exchange) throws IOException {
            method = exchange.getRequestMethod();
            contentType = exchange.getRequestHeaders().getFirst("Content-Type");
            traceId = exchange.getRequestHeaders().getFirst("X-Trace-ID");
            try (InputStream in = exchange.getRequestBody()) {
                body = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            }
            byte[] bytes = responseBody.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(responseStatus, bytes.length);
            exchange.getResponseBody().write(bytes);
            exchange.close();
        }

        @Override
        public void close() { server.stop(0); }
    }
}
