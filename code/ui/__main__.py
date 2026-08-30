import sys
from pathlib import Path

from streamlit.web import cli as stcli

from code.paths import ROOT

if __name__ == "__main__":
    app = ROOT / "code" / "ui" / "app.py"
    raise SystemExit(stcli.main(["--", "run", str(app), *sys.argv[1:]]))