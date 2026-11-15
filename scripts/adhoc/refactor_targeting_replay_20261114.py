"""Extract pure packet targeting for launcher replay; PR94/#96, 2026-11-14.

Input/output: edge_recanary_20261113/source_adjudicate.py on this branch.
One-time mechanical dedent preserves the existing extraction decisions.
"""

from pathlib import Path

path = Path(__file__).parent / 'edge_recanary_20261113/source_adjudicate.py'
text = path.read_text()
if 'def packet_targeting(packet):' in text:
    raise SystemExit('The one-time extraction is already applied; no files changed')
start = text.index('def targeting(source_dir, output, ordinal=None):')
body_start = text.index('        edge = packet["edge"]', start)
body_end = text.index('    Path(output).write_text', body_start)
body = ''.join(line[4:] if line.startswith('    ') else line
               for line in text[body_start:body_end].splitlines(keepends=True))
body = body.replace('    result.append(\n', '    return (\n', 1)
wrapper = '''def packet_targeting(packet):
    """Rebuild targeting solely from one retained source packet."""
'''
wrapper += body
wrapper += '''

def targeting(source_dir, output, ordinal=None):
    if Path(output).exists():
        raise ValueError("Refusing to overwrite existing targeting evidence")
    packets = sorted((Path(source_dir) / "packets").glob("*.json"))
    if ordinal is not None:
        packets = [private_packet(source_dir, ordinal)]
    result = []
    for path in packets:
        packet = json.loads(path.read_text())
        result.append({**packet_targeting(packet), "source_packet": packet})
'''
path.write_text(text[:start] + wrapper + text[body_end:])
