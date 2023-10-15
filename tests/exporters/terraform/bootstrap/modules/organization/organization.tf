resource "tfe_organization" "organization" {
  email = "admin@example.com"
  name  = var.name
}
