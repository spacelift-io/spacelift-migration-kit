FROM hashicorp/terraform:1.5.6 as terraform
FROM ubuntu:24.04

WORKDIR /app

COPY main.tf /app/main.tf
COPY entrypoint.sh /app/entrypoint.sh
COPY --from=terraform /bin/terraform /bin/terraform

RUN mkdir -p $HOME/.terraform.d && chmod +x entrypoint.sh
RUN DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl

ENTRYPOINT ["/app/entrypoint.sh"]
