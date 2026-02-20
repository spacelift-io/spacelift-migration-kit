"""Pydantic models for plugin configuration schema."""

from typing import Literal

from pydantic import BaseModel


class ConfigFieldDependency(BaseModel):
    field: str  # key of the controlling field
    value: str  # show this field only when controlling field equals this value


class ConfigField(BaseModel):
    key: str
    label: str
    type: Literal["password", "select", "text", "url"]
    required: bool = True
    depends_on: ConfigFieldDependency | None = None
    help_text: str = ""
    options: list[dict[str, str]] = []  # for type="select"
    placeholder: str = ""


class SourcePluginInfo(BaseModel):
    description: str = ""
    display_name: str
    fields: list[ConfigField] = []
    plugin_id: str
