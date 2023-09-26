class CodePublisher:
    def __init__(self, config, console):
        self._config = config
        self._console = console

    def publish(self):
        """Push the Terraform source code to manage Spacelift entities to a git repository"""
        self._console.print(f"{self.__class__.__name__}.publish()")
