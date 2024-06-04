terraform {
  cloud {
    organization = "{replace_me}"

    workspaces {
      name = "SMK"
    }
  }
}

resource "null_resource" "nothing" {
  triggers = {
    always_run = timestamp()
  }
}
