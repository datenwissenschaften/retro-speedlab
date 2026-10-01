readonly SETTINGS_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/config.yaml"

setting() {
    python3 - "${SETTINGS_PATH}" "$1" <<'PYTHON'
import sys

import yaml

value = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
for key in sys.argv[2].split("."):
    value = value[key]
print(value)
PYTHON
}
