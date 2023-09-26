class Generator:
    def __init__(self, config, console):
        self._config = config
        self._console = console

    def generate(self):
        """Generate source code for managing Spacelift entities"""
        self._console.print(f"{self.__class__.__name__}.generate()")
