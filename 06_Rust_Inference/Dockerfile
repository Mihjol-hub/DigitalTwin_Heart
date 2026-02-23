FROM rust:latest as builder
WORKDIR /usr/src/app

# Dependencies for build
RUN apt-get update && apt-get install -y pkg-config libssl-dev ca-certificates curl && rm -rf /var/lib/apt/lists/*

COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
WORKDIR /app

# Dependencies for production
RUN apt-get update && apt-get install -y ca-certificates libgomp1 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/src/app/target/release/anesthesia_inference .
COPY --from=builder /usr/src/app/anesthesia_model.onnx .

EXPOSE 8080
CMD ["./anesthesia_inference"]