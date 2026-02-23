"""Tests for config manager."""

from pathlib import Path

import pytest
import yaml

from smk.core.config.manager import ConfigManager, is_config_initialized, load_config, require_config_initialized
from smk.core.config.models import SMKConfig
from smk.core.exceptions import ConfigNotInitializedError


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_init_with_default_dir(self):
        """ConfigManager should use default dir when none provided."""
        manager = ConfigManager()
        assert manager.config_dir.name == "smk"

    def test_init_with_custom_dir(self, tmp_path: Path):
        """ConfigManager should use custom dir when provided."""
        manager = ConfigManager(tmp_path)
        assert manager.config_dir == tmp_path

    def test_config_file_property(self, tmp_path: Path):
        """config_file should return path to config.yaml."""
        manager = ConfigManager(tmp_path)
        assert manager.config_file == tmp_path / "config.yaml"

    def test_data_dir_property(self, tmp_path: Path):
        """data_dir should return path to data directory."""
        manager = ConfigManager(tmp_path)
        assert manager.data_dir == tmp_path / "data"

    def test_logs_dir_property(self, tmp_path: Path):
        """logs_dir should return path to logs directory."""
        manager = ConfigManager(tmp_path)
        assert manager.logs_dir == tmp_path / "logs"

    def test_is_initialized_false(self, tmp_path: Path):
        """is_initialized should return False when config doesn't exist."""
        manager = ConfigManager(tmp_path)
        assert manager.is_initialized is False

    def test_is_initialized_true(self, tmp_path: Path):
        """is_initialized should return True when config exists."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("config_version: 1\n")
        manager = ConfigManager(tmp_path)
        assert manager.is_initialized is True

    def test_require_initialized_raises(self, tmp_path: Path):
        """require_initialized should raise when not initialized."""
        manager = ConfigManager(tmp_path)
        with pytest.raises(ConfigNotInitializedError) as exc_info:
            manager.require_initialized()
        assert str(tmp_path) in str(exc_info.value)

    def test_require_initialized_passes(self, tmp_path: Path):
        """require_initialized should not raise when initialized."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("config_version: 1\n")
        manager = ConfigManager(tmp_path)
        manager.require_initialized()  # Should not raise


class TestConfigManagerInit:
    """Tests for ConfigManager.init method."""

    def test_init_creates_directories(self, tmp_path: Path):
        """init should create all required directories."""
        manager = ConfigManager(tmp_path)
        manager.init()

        assert (tmp_path / "config.yaml").exists()
        assert (tmp_path / "logs").is_dir()
        assert (tmp_path / "data" / "generated").is_dir()
        assert (tmp_path / "data" / "source").is_dir()
        assert (tmp_path / "data" / "transformed").is_dir()

    def test_init_creates_config_file(self, tmp_path: Path):
        """init should create valid config file."""
        manager = ConfigManager(tmp_path)
        config = manager.init()

        assert config.config_version == 1
        assert manager.config_file.exists()

        # Verify YAML content
        with manager.config_file.open() as f:
            data = yaml.safe_load(f)
        assert data["config_version"] == 1

    def test_init_with_values(self, tmp_path: Path):
        """init should save provided values."""
        manager = ConfigManager(tmp_path)
        config = manager.init(
            source_plugin="terraform-cloud",
            spacelift_endpoint="https://example.app.spacelift.io",
            spacelift_key_id="key123",
            spacelift_key_secret="secret456",
        )

        assert config.source.plugin == "terraform-cloud"
        assert config.spacelift.api_endpoint == "https://example.app.spacelift.io"
        assert config.spacelift.api_key_id == "key123"
        assert config.spacelift.api_key_secret == "secret456"

    def test_init_raises_if_exists(self, tmp_path: Path):
        """init should raise FileExistsError if config exists."""
        manager = ConfigManager(tmp_path)
        manager.init()

        with pytest.raises(FileExistsError) as exc_info:
            manager.init()
        assert "--force" in str(exc_info.value)

    def test_init_force_overwrites(self, tmp_path: Path):
        """init with force should overwrite existing config."""
        manager = ConfigManager(tmp_path)
        manager.init(source_plugin="old-plugin")
        manager.init(force=True, source_plugin="new-plugin")

        config = manager.load()
        assert config.source.plugin == "new-plugin"


class TestConfigManagerState:
    """Tests for ConfigManager load_state and save_state methods."""

    def test_load_state_defaults_when_missing(self, tmp_path: Path):
        """load_state should return start/start when state file missing."""
        manager = ConfigManager(tmp_path)
        state = manager.load_state()
        assert state == {"furthest_step": "start", "last_step": "start"}

    def test_load_state_reads_both_fields(self, tmp_path: Path):
        """load_state should return both last_step and furthest_step."""
        manager = ConfigManager(tmp_path)
        manager.save_state(last_step="configure", furthest_step="export")
        state = manager.load_state()
        assert state == {"furthest_step": "export", "last_step": "configure"}

    def test_load_state_migrates_old_format(self, tmp_path: Path):
        """load_state should use last_step as furthest_step for old state.yaml."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("last_step: export\n")
        manager = ConfigManager(tmp_path)
        state = manager.load_state()
        assert state == {"furthest_step": "export", "last_step": "export"}

    def test_load_state_defaults_on_corrupt_file(self, tmp_path: Path):
        """load_state should return start/start on unreadable file."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("not: valid: yaml: [[[")
        manager = ConfigManager(tmp_path)
        # corrupt YAML may or may not raise; we just want safe defaults
        state = manager.load_state()
        assert state["last_step"] == "start"
        assert state["furthest_step"] == "start"

    def test_save_state_creates_file(self, tmp_path: Path):
        """save_state should create state.yaml with both fields."""
        manager = ConfigManager(tmp_path)
        manager.save_state(last_step="configure", furthest_step="export")
        with (tmp_path / "state.yaml").open() as f:
            data = yaml.safe_load(f)
        assert data == {"furthest_step": "export", "last_step": "configure"}

    def test_save_state_uses_sort_keys(self, tmp_path: Path):
        """save_state should write keys in alphabetical order."""
        manager = ConfigManager(tmp_path)
        manager.save_state(last_step="configure", furthest_step="export")
        raw = (tmp_path / "state.yaml").read_text()
        assert raw.index("furthest_step") < raw.index("last_step")

    def test_save_state_creates_dir_if_missing(self, tmp_path: Path):
        """save_state should create config dir when it doesn't exist."""
        config_dir = tmp_path / "nonexistent"
        manager = ConfigManager(config_dir)
        manager.save_state(last_step="start", furthest_step="start")
        assert (config_dir / "state.yaml").exists()


class TestConfigManagerLoadSave:
    """Tests for ConfigManager load and save methods."""

    def test_load_returns_config(self, tmp_path: Path):
        """load should return SMKConfig from file."""
        manager = ConfigManager(tmp_path)
        manager.init(source_plugin="test-plugin")

        loaded = manager.load()
        assert isinstance(loaded, SMKConfig)
        assert loaded.source.plugin == "test-plugin"

    def test_load_raises_if_not_initialized(self, tmp_path: Path):
        """load should raise ConfigNotInitializedError if not initialized."""
        manager = ConfigManager(tmp_path)
        with pytest.raises(ConfigNotInitializedError):
            manager.load()

    def test_save_updates_file(self, tmp_path: Path):
        """save should update the config file."""
        manager = ConfigManager(tmp_path)
        manager.init()

        config = manager.load()
        config.source.plugin = "updated-plugin"
        manager.save(config)

        reloaded = manager.load()
        assert reloaded.source.plugin == "updated-plugin"


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_is_config_initialized_false(self, tmp_path: Path):
        """is_config_initialized should return False when not initialized."""
        assert is_config_initialized(tmp_path) is False

    def test_is_config_initialized_true(self, tmp_path: Path):
        """is_config_initialized should return True when initialized."""
        ConfigManager(tmp_path).init()
        assert is_config_initialized(tmp_path) is True

    def test_require_config_initialized_raises(self, tmp_path: Path):
        """require_config_initialized should raise when not initialized."""
        with pytest.raises(ConfigNotInitializedError):
            require_config_initialized(tmp_path)

    def test_require_config_initialized_passes(self, tmp_path: Path):
        """require_config_initialized should not raise when initialized."""
        ConfigManager(tmp_path).init()
        require_config_initialized(tmp_path)  # Should not raise

    def test_load_config_returns_config(self, tmp_path: Path):
        """load_config should return SMKConfig."""
        ConfigManager(tmp_path).init(source_plugin="test")
        config = load_config(tmp_path)
        assert config.source.plugin == "test"

    def test_load_config_raises_if_not_initialized(self, tmp_path: Path):
        """load_config should raise ConfigNotInitializedError if not initialized."""
        with pytest.raises(ConfigNotInitializedError):
            load_config(tmp_path)
