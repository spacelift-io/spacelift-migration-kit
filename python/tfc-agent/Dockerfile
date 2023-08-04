FROM hashicorp/tfc-agent:latest

COPY --chmod=755 --chown=tfc-agent:tfc-agent <<EOF /home/tfc-agent/.tfc-agent/hooks/terraform-pre-plan
#!/bin/bash
echo '<==================== TFC EXPORT: ENVIROMNENT VARIABLES ===================='
env
echo '==================== TFC EXPORT: ENVIROMNENT VARIABLES ====================>'
EOF
