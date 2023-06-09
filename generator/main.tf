terraform {
  required_version = "~> 1.2"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4.0"
    }
  }
}

locals {
  #  Use custom template file, if present
  template_file = fileexists("${path.module}/../generator.tftpl") ? "${path.module}/../generator.tftpl" : "${path.module}/generator.tftpl"
}

resource "local_file" "terraform" {
  content  = templatefile(local.template_file, { stacks = var.stacks })
  filename = "${path.module}/../out/main.tf"

  provisioner "local-exec" {
    command = "terraform fmt ${self.filename}"
  }
}
