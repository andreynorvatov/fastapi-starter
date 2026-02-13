# Stage 1: Get timezone data
FROM alpine:3.20 AS tzdata
RUN apk add --no-cache tzdata

# Stage 2: MinIO with Moscow timezone
FROM minio/minio:latest

# Set timezone environment variable
ENV TZ=Europe/Moscow

# Create zoneinfo directory
RUN mkdir -p /usr/share/zoneinfo

# Copy Moscow timezone data from the tzdata stage
COPY --from=tzdata /usr/share/zoneinfo/Europe/Moscow /usr/share/zoneinfo/Europe/Moscow

# Set localtime and timezone
RUN cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone

# The MinIO server will be started via command from docker-compose
CMD ["minio"]