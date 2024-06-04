#!/bin/bash

# Ensure the terraform rc directory is setup properly
if ! test -f $HOME/.terraform.d/credentials.tfrc.json; then
  echo "No Credentials for TFC found, exiting."
  exit 1
fi

sed -i -e "s/{replace_me}/$ORG/g" main.tf

terraform init
terraform apply --auto-approve
