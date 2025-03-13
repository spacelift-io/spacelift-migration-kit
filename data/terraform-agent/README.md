# Custom Terraform Agent

This custom Terraform agent outputs the local environment variables so that they get captured in the run logs and the value of sensitive variables can be extracted.

## Using the default Docker image

The default Docker image will be automatically pulled and used. There is no need for additional configuration.

## Using a custom Docker image

If you are unable to use the default Docker image, you can build and use a custom image.

### Build the image

```shell
cd data/terraform-agent
docker build --build-arg TFC_AGENT_VERSION=<VERSION> --platform linux/amd64 --tag ghcr.io/spacelift-io/spacelift-migration-kit:latest .
```

### Publish the image

This step is optional. If Spacelift Migration Kit is run on a single machine, this step can be skipped.

```shell
docker push ghcr.io/spacelift-io/spacelift-migration-kit:latest
```

### Update the configuration file

Set the following key in the `config.yml` file:

```yaml
exporter:
  settings:
    agent_image: <TAG>
```
