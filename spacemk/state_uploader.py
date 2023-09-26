class StateUploader:
    def __init__(self, config, console):
        self._config = config
        self._console = console

    def upload_state_files(self):
        """Upload Terraform state files to state backend"""
        self._console.print(f"{self.__class__.__name__}.upload_state_files()")
