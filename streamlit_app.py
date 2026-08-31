"""Entry point for Streamlit Community Cloud.

Community Cloud looks for a top-level app file (streamlit_app.py / app.py).
This delegates to the real app in code/ui/app.py.
"""
import pathlib
import runpy

ROOT = pathlib.Path(__file__).resolve().parent
runpy.run_path(str(ROOT / "code" / "ui" / "app.py"), run_name="__main__")
