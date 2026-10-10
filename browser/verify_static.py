"""Verify the exact static publication against its build manifest."""

import argparse
import hashlib
import json
from pathlib import Path


def verify(dist):
    manifest = json.loads((dist / "manifest.json").read_text())
    config = json.loads((dist / "app.json").read_text())
    assert config["requirements"] == [], (
        "Server packages must not be installed into stlite"
    )
    assert config["sharedWorker"] is False, "Each tab must have its own worker"
    for name, expected in manifest["source_sha256"].items():
        assert hashlib.sha256(config["files"][name].encode()).hexdigest() == expected, (
            name
        )
        assert hashlib.sha256((dist / name).read_bytes()).hexdigest() == expected, name
    for asset in manifest["runtime"]["assets"]:
        directory = (
            "pyodide"
            if asset["url"].startswith("https://cdn.jsdelivr.net/pyodide/")
            else "python"
        )
        path = dist / "vendor" / directory / asset["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == asset["sha256"], path
        assert path.stat().st_size == asset["bytes"], path
    for name, expected in manifest["static_sha256"].items():
        assert hashlib.sha256((dist / name).read_bytes()).hexdigest() == expected, name
    assert (dist / ".nojekyll").is_file()
    print(
        f"Verified {len(manifest['static_sha256'])} static files and all {len(manifest['source_sha256'])} packaged Python modules."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dist", type=Path, default=Path(__file__).resolve().parent / "dist"
    )
    verify(parser.parse_args().dist)
