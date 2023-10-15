terraform {
  required_version = "~> 1.0"

  required_providers {
    tfe = {
      source  = "hashicorp/tfe"
      version = "~> 0.49.2"
    }
  }
}

provider "tfe" {
  token = var.api_token
}
