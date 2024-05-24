FROM python:3.12-slim-bookworm

# Update system packages and install dependencies
# hadolint ignore=DL3008
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get -y upgrade \
    && apt-get install --no-install-recommends -y docker.io unzip wget \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/*

# Install Terraform
ENV TERRAFORM_VERSION=1.5.7
RUN wget -qO /tmp/terraform.zip https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    && unzip /tmp/terraform.zip -d /usr/local/bin \
    && rm /tmp/terraform.zip

# Cache Spacelift Terraform provider
COPY data/smk-docker/.terraformrc /root/.terraformrc
ENV SPACELIFT_TERRAFORM_PROVIDER_VERSION=1.10.0
RUN mkdir -p /usr/share/terraform/providers/registry.terraform.io/spacelift-io/spacelift/ \
    && wget -qO /usr/share/terraform/providers/registry.terraform.io/spacelift-io/spacelift/terraform-provider-spacelift_${SPACELIFT_TERRAFORM_PROVIDER_VERSION}_linux_amd64.zip \
    https://github.com/spacelift-io/terraform-provider-spacelift/releases/download/v${SPACELIFT_TERRAFORM_PROVIDER_VERSION}/terraform-provider-spacelift_${SPACELIFT_TERRAFORM_PROVIDER_VERSION}_linux_amd64.zip

# Install Poetry
ENV POETRY_VERSION=1.8.3
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

# Install spacemk command and dependencies
WORKDIR /app
COPY . ./
RUN poetry --no-interaction install --no-cache --without dev
ENTRYPOINT ["poetry", "run", "spacemk"]
