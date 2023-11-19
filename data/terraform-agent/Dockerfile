ARG TFC_AGENT_VERSION=latest

FROM hashicorp/tfc-agent:${TFC_AGENT_VERSION}

COPY terraform-pre-plan /home/tfc-agent/.tfc-agent/hooks/terraform-pre-plan

USER root
RUN chmod +x /home/tfc-agent/.tfc-agent/hooks/terraform-pre-plan
USER tfc-agent
