"""Isolated OCR subprocess. Local verified models only; JSON on stdout."""
import json, sys
from pathlib import Path
from hashlib import sha256
import socket
# Inference is intentionally network-independent, including lazy dependency calls.
def no_network(*args, **kwargs):
    raise RuntimeError('Network disabled in receipt OCR')
socket.socket.connect = no_network
socket.create_connection = no_network
from PIL import Image, ImageOps
from receipt_image import isolate_receipt, ReceiptBoundaryError
import numpy as np
import onnxruntime
onnxruntime.disable_telemetry_events()
from rapidocr import RapidOCR
root=Path(__file__).resolve().parents[1]
models=root/'backend/.ocr-models'
manifest=json.loads((root/'tools/receipt-models.json').read_text())
for name, digest in manifest.items():
    assert sha256((models/name).read_bytes()).hexdigest()==digest,'OCR model checksum mismatch'
engine=RapidOCR(params={'Global.log_level':'critical',
 'Det.model_path':str(models/'PP-OCRv6_det_small.onnx'),
 'Cls.model_path':str(models/'ch_ppocr_mobile_v2.0_cls_mobile.onnx'),
 'Rec.model_path':str(models/'PP-OCRv6_rec_small.onnx'),
 'EngineConfig.onnxruntime.intra_op_num_threads':2,'EngineConfig.onnxruntime.inter_op_num_threads':1})
with Image.open(sys.argv[1]) as source:
    image=ImageOps.exif_transpose(source).convert('RGB')
    image.thumbnail((2000,3000))
    try:
        pixels=isolate_receipt(np.asarray(image))
    except ReceiptBoundaryError:
        print(json.dumps({'error':'receipt_boundary'}))
        sys.exit(0)
    result=engine(pixels[:,:,::-1])
sys.path.insert(0,str(root/'backend'))
from pigpen.receipt_layout import group_rows
tokens=[]
if result.txts:
    for box,text,score in zip(result.boxes,result.txts,result.scores):
        width=float(box[:,0].max()-box[:,0].min())
        tokens.append({'x':float(box[:,0].min()),'center_x':float(box[:,0].mean()),
                       'raw_y':float(box[:,1].mean()),'width':width,
                       'height':float((np.linalg.norm(box[3]-box[0])+np.linalg.norm(box[2]-box[1]))/2),
                       'slope':float((box[1,1]-box[0,1])/max(box[1,0]-box[0,0],1)),
                       'text':str(text),'score':float(score)})
print(json.dumps(group_rows(tokens)))
