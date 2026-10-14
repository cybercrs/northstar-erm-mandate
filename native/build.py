"""Build only the native files; publication installs this directory under /js/."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
FILES = ('index.html','style.css','content.js','snapshot.js','random.js','engine.js','app.js')


def build(output):
    output.mkdir(parents=True,exist_ok=True)
    hashes={};sizes={}
    for name in FILES:
        data=(HERE/name).read_bytes();(output/name).write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest();sizes[name]=len(data)
    manifest={'files_sha256':hashes,'files_bytes':sizes,'application_bytes':sum(sizes.values()),'runtime_dependencies':[],
              'entrypoint':'index.html','canonical_directory':'js/','teaching_source':'11d3064dd429c0f2cf4c6a7255c3eaf61cd75dc5'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2));return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=HERE/'dist');args=parser.parse_args();build(args.output)
