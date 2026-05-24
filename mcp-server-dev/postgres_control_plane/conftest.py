"""pytest config: make postgres_control_plane importable when running tests from inside the package dir."""
import sys
from pathlib import Path

# Add mcp-server-dev/ (the parent of postgres_control_plane/) to sys.path
# so that `import postgres_control_plane` works.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
