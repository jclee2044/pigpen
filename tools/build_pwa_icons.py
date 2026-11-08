"""Compose app icons from the existing stacked logo using installed rsvg-convert."""
from pathlib import Path
import copy
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = 'http://www.w3.org/2000/svg'
BACKGROUND = '#f2dde4'
ET.register_namespace('', SVG)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')


def tag(name):
    return f'{{{SVG}}}{name}'


svg = ET.Element(tag('svg'), {
    # Crop the design's paper margin so the stacked artwork fills more of the icon.
    'viewBox': '130 130 940 940', 'width': '512', 'height': '512',
})
ET.SubElement(svg, tag('rect'), {
    'width': '1200', 'height': '1200', 'fill': BACKGROUND,
})
defs = ET.SubElement(svg, tag('defs'))
# Darken replaces the master's pale paper with pink while retaining its darker ink.
filter_node = ET.SubElement(defs, tag('filter'), {
    'id': 'pink-paper', 'color-interpolation-filters': 'sRGB',
    'x': '0', 'y': '0', 'width': '100%', 'height': '100%',
})
ET.SubElement(filter_node, tag('feFlood'), {
    'flood-color': BACKGROUND, 'result': 'paper',
})
ET.SubElement(filter_node, tag('feBlend'), {
    'in': 'SourceGraphic', 'in2': 'paper', 'mode': 'darken',
})
stacked = ET.parse(ROOT / 'design/logo-concepts-v11/pigpen-stacked.svg').getroot()
logo = ET.SubElement(svg, tag('g'), {
    'transform': 'translate(0 75)', 'filter': 'url(#pink-paper)',
})
for child in stacked:
    logo.append(copy.deepcopy(child))

output = ROOT / 'frontend/public/icons'
output.mkdir(parents=True, exist_ok=True)
source = output / 'pigpen.svg'
source.write_bytes(ET.tostring(svg, encoding='utf-8', xml_declaration=True))


def render(size, destination):
    subprocess.run([
        'rsvg-convert', '-w', str(size), '-h', str(size),
        '-o', str(destination), str(source),
    ], check=True)


for size in (180, 192, 512):
    render(size, output / f'icon-{size}.png')

# ICO supports PNG frames; keep the conventional fallback in sync as well.
with tempfile.TemporaryDirectory(dir=output) as temporary:
    frames = []
    for size in (16, 32, 48):
        path = Path(temporary) / f'{size}.png'
        render(size, path)
        frames.append((size, path.read_bytes()))
    offset = 6 + 16 * len(frames)
    entries = []
    for size, data in frames:
        entries.append(struct.pack('<BBBBHHII', size, size, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    (output.parent / 'favicon.ico').write_bytes(
        struct.pack('<HHH', 0, 1, len(frames))
        + b''.join(entries) + b''.join(data for _, data in frames)
    )
