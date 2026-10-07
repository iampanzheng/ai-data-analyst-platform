# syntax=docker/dockerfile:1.7

FROM maven:3.9-eclipse-temurin-21 AS build

WORKDIR /workspace

COPY backend/springboot/pom.xml .

RUN --mount=type=cache,target=/root/.m2 \
    --mount=type=secret,id=maven_settings,target=/root/.m2/settings.xml,required=false \
    mvn -q -DskipTests dependency:go-offline

COPY backend/springboot/src src

RUN --mount=type=cache,target=/root/.m2 \
    --mount=type=secret,id=maven_settings,target=/root/.m2/settings.xml,required=false \
    mvn -q -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
ENV HOME=/tmp
COPY --from=build --chown=10001:10001 /workspace/target/ai-data-analyst-gateway-0.1.0-SNAPSHOT.jar /app/app.jar
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
