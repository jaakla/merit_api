from importlib.metadata import PackageNotFoundError, version

from .client import MeritAPI
from .exceptions import MeritAPIError

try:
    __version__ = version("merit-api")
except PackageNotFoundError:  # pragma: no cover - editable/source checkout without metadata
    __version__ = "0.0.0+unknown"

__all__ = ["MeritAPI", "MeritAPIError", "__version__"]
