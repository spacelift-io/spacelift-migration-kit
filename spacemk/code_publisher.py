import click


class CodePublisher:
    def __init__(self, config):
        self._config = config

    def publish(self):
        """Push the Terraform source code to manage Spacelift entities to a git repository"""
        click.echo("Please, review the source code generated in the 'tmp/code' folder and edit it as needed.")
        click.echo("Then, commit it and push it to a git repository that is available to your Spacelift account.")
