FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /workspace
COPY backend/springboot/pom.xml .
RUN mvn -q -DskipTests dependency:go-offline
COPY backend/springboot/src src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /workspace/target/ai-data-analyst-gateway-0.1.0-SNAPSHOT.jar /app/app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
