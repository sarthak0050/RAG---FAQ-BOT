def __getattr__(name: str):
    if name in {"EXAMPLES", "DISCLAIMER", "WELCOME"}:
        from code.ui import app

        return getattr(app, name)
    raise AttributeError(f"module 'code.ui' has no attribute {name!r}")


__all__ = ["EXAMPLES", "DISCLAIMER", "WELCOME"]