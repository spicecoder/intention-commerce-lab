FROM maven:3.9.9-eclipse-temurin-17 AS build
WORKDIR /service
COPY pom.xml ./
RUN mvn -q -DskipTests dependency:go-offline
COPY src ./src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:17-jre-jammy
WORKDIR /service
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=build /service/target/inventory-spring-0.1.0.jar /service/application.jar
EXPOSE 8081
USER 10001
CMD ["java", "-jar", "/service/application.jar"]
