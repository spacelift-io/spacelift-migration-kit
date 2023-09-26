class Importer:
    def __init__(self, config, console):
        self._config = config
        self._console = console

    def _create_entitites(self):
        """Trigger Spacelift manager stack to create entities"""
        self._console.print(f"{self.__class__.__name__}._create_entitites()")

    def _create_manager_stack(self):
        """Create Spacelift manager stack"""
        self._console.print(f"{self.__class__.__name__}._create_manager_stack()")

    def create(self):
        """Create Spacelift manager stack and entities"""
        self._console.print(f"{self.__class__.__name__}.create()")
        self._create_manager_stack()
        self._create_entitites()
