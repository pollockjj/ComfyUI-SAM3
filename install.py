from __future__ import annotations

import json

from installer import install_everything


if __name__ == "__main__":
    print(json.dumps(install_everything(), indent=2, sort_keys=True))
