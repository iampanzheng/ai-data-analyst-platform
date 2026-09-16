package com.aianalyst.gateway.service;

import org.junit.jupiter.api.Test;

import java.lang.reflect.Method;

import static org.junit.jupiter.api.Assertions.assertEquals;

class FastApiClientJsonTest {

    @Test
    void serializesSqlAsJson() throws Exception {
        Method method = FastApiClient.class.getDeclaredMethod(
                "toJsonSql",
                String.class
        );
        method.setAccessible(true);

        String json = (String) method.invoke(null, "SELECT 1");

        assertEquals("{\"sql\":\"SELECT 1\"}", json);
    }

    @Test
    void escapesJsonCharacters() throws Exception {
        Method method = FastApiClient.class.getDeclaredMethod(
                "toJsonSql",
                String.class
        );
        method.setAccessible(true);

        String json = (String) method.invoke(
                null,
                "SELECT \"name\"\nFROM city"
        );

        assertEquals(
                "{\"sql\":\"SELECT \\\"name\\\"\\nFROM city\"}",
                json
        );
    }
}