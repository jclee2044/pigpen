"""Compose install icons from PigPen's existing SVG layers; no new artwork."""
from pathlib import Path
import copy
import subprocess
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
SVG='http://www.w3.org/2000/svg'
ET.register_namespace('',SVG)
svg=ET.Element('{'+SVG+'}svg',{'viewBox':'0 0 512 512','width':'512','height':'512'})
ET.SubElement(svg,'{'+SVG+'}rect',{'width':'512','height':'512','fill':'#fff1d8'})
group=ET.SubElement(svg,'{'+SVG+'}g',{'transform':'translate(58 58) scale(.775)'})
for name in ['base/pig.svg','bandana/grass.svg']:
    for child in ET.parse(ROOT/'assets/avatars/pig-v1'/name).getroot():group.append(copy.deepcopy(child))
output=ROOT/'frontend/public/icons';output.mkdir(parents=True,exist_ok=True)
source=output/'pigpen.svg';source.write_bytes(ET.tostring(svg,encoding='utf-8',xml_declaration=True))
for size in [180,192,512]:subprocess.run(['rsvg-convert','-w',str(size),'-h',str(size),'-o',str(output/f'icon-{size}.png'),str(source)],check=True)
