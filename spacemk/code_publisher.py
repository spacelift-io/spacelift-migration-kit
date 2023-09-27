class CodePublisher:
    def __init__(self, config, console):
        self._config = config
        self._console = console

    def publish(self):
        """Push the Terraform source code to manage Spacelift entities to a git repository"""
        self._console.print(
            "Please, review the source code generated in the [path]tmp/code[/path] folder and edit it as needed."
        )
        self._console.print(
            "Then, commit it and push it to a git repository that is available to your Spacelift account."
        )
