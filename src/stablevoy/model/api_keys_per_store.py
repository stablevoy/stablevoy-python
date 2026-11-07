from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class ApiKeysPerStore:
    """How many active API keys one store may hold per integration; revoked keys do not count."""

    plugin: int
    """Keys of one plugin (WooCommerce, Easy Digital Downloads, WHMCS)."""
    mcp: int
    """AI assistant (MCP) keys, one per computer."""
    api: int
    """Keys for your own code."""

    @classmethod
    def from_fields(cls, f: Fields) -> ApiKeysPerStore:
        return cls(f.integer("plugin"), f.integer("mcp"), f.integer("api"))
