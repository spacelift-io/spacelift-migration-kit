ARG TFC_AGENT_VERSION=latest

FROM hashicorp/tfc-agent:${TFC_AGENT_VERSION}

COPY --chmod=755 --chown=tfc-agent:tfc-agent terraform-pre-plan /home/tfc-agent/.tfc-agent/hooks/terraform-pre-plan
