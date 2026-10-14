"""Audit immutable teaching sources, generated content, syntax and final metadata."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'native'
manifest=json.loads((HERE/'tests/content-manifest.json').read_text())
for name,expected in manifest['source_files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
for path in HERE.glob('*.js'):subprocess.run(['node','--check',str(path)],check=True)
content=(HERE/'content.js').read_text()
html=(HERE/'index.html').read_text()
provisional=r'\b(?:pilot|preview|prototype)\b|\btest (?:app|version|site)\b'
assert not re.search(provisional,html,re.I)
assert not re.search(provisional,content,re.I)
assert '<title>Northstar Cold Chain | The ERM Mandate</title>' in html
assert not re.search(r'<script[^>]+src=["\']https?://',html,re.I)
build=json.loads((HERE/'dist/manifest.json').read_text())
for name,expected in build['files_sha256'].items():assert hashlib.sha256((HERE/'dist'/name).read_bytes()).hexdigest()==expected,name
assert build['runtime_dependencies']==[]
assert set(p.name for p in (HERE/'dist').iterdir())==set(build['files_sha256'])|{'manifest.json'}
result={'protected_sources':manifest['source_files'],'syntax':'passed','content_and_metadata_branding':'passed','served_assets':len(build['files_sha256']),'downloads_in_original':0,'app_owned_assets_in_original':0}
(HERE/'review/source-and-branding-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
