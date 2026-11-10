"""Provision bundled, version-pinned OCR models; never called by the web app."""
from pathlib import Path
from hashlib import sha256
import json, shutil
import rapidocr
root=Path(__file__).resolve().parents[1]/'backend/.ocr-models'
root.mkdir(exist_ok=True)
for p in (Path(rapidocr.__file__).parent/'models').glob('*.onnx'):
    shutil.copyfile(p,root/p.name)
models={p.name:sha256(p.read_bytes()).hexdigest() for p in root.glob('*.onnx')}
assert len(models)==3,models
expected=Path(__file__).with_name('receipt-models.json')
if expected.exists():
    assert models==json.loads(expected.read_text()), 'Pinned model checksum mismatch'
(root/'manifest.json').write_text(json.dumps(models,indent=2)+'\n')
print(json.dumps(models,indent=2))
