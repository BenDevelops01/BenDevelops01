"""Remove snk's eaten-contribution bar while keeping the grid animation."""

from pathlib import Path
import math
import re
import sys
import xml.etree.ElementTree as ET

ET.register_namespace("", "http://www.w3.org/2000/svg")

for filename in sys.argv[1:]:
    path = Path(filename)
    root = ET.fromstring(path.read_text())
    removed = 0
    for parent in root.iter():
        for child in list(parent):
            if "u" in child.get("class", "").split():
                parent.remove(child)
                removed += 1
    if removed:
        x, y, width, height = map(float, root.attrib["viewBox"].split())
        css = "".join(element.text or "" for element in root if element.tag.endswith("style"))
        cell_size = re.search(r"\.c\{[^}]*height:([\d.]+)px", css)
        cell_height = float(cell_size.group(1)) if cell_size else 16
        grid_bottom = max(float(e.get("y", 0)) + cell_height for e in root.iter() if "c" in e.get("class", "").split())
        snake_height = max(float(e.get("height", 0)) for e in root.iter() if "s" in e.get("class", "").split())
        snake_positions = [float(value) for value in re.findall(r"translate\(\s*[-\d.]+px,\s*([-\d.]+)px\)", css)]
        snake_bottom = max(snake_positions, default=grid_bottom) + snake_height
        cropped_height = min(height, math.ceil((max(grid_bottom, snake_bottom) + 16 - y) / 16) * 16)
        root.set("viewBox", " ".join(f"{n:g}" for n in (x, y, width, cropped_height)))
        root.set("height", f"{cropped_height:g}")
        path.write_text(ET.tostring(root, encoding="unicode"))
