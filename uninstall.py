from __future__ import annotations

import json

from installer import uninstall_everything


if __name__ == "__main__":
    print(json.dumps(uninstall_everything(), indent=2, sort_keys=True))
