resource "tfe_agent_pool" "agent_pool_1" {
  name                = "smk-agent-pool-1"
  organization        = tfe_organization.organization.name
  organization_scoped = true
}

resource "tfe_agent_pool" "agent_pool_2" {
  name                = "smk-agent-pool-2"
  organization        = tfe_organization.organization.name
  organization_scoped = false
}
