"""Federation module for cross-repo lesson sync."""

from .registry import FederationRegistry, PeerNode
from .sync_protocol import FederationSync, LessonManifest, SyncResult

__all__ = [
    "FederationRegistry",
    "PeerNode",
    "FederationSync",
    "LessonManifest",
    "SyncResult",
]
