# Day 4 Fix 3 — RestClient Builder bean missing

Root cause: Spring Boot 4.1.1 provides RestClient auto-configuration through the dedicated `spring-boot-starter-restclient`. The gateway `pom.xml` only included `spring-boot-starter-web`, so no `RestClient.Builder` bean was available for `FastApiClient`.

Fix: add `org.springframework.boot:spring-boot-starter-restclient` to the gateway Maven dependencies. Keep `FastApiClient` injecting the Boot-managed `RestClient.Builder`.

This is preferable to creating a custom builder because Spring Boot's RestClient auto-configuration also wires message conversion and related defaults.
