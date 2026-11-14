"""Render a GitHub contribution calendar as a native animated SVG.

Only public calendar data is used. No credentials, JavaScript, or GIFs are needed.
"""

from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import argparse
import json
import math
import re
import time
from urllib.request import Request, urlopen


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tooltip = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "data-date" in attrs:
            weekday, week = map(int, attrs["id"].split("-")[-2:])
            self.cells[attrs["id"]] = {
                "x": week, "y": weekday, "date": attrs["data-date"],
                "level": int(attrs["data-level"]), "count": 0,
            }
        elif tag == "tool-tip":
            self.tooltip = attrs.get("for")

    def handle_data(self, value):
        if self.tooltip in self.cells:
            match = re.match(r"([\d,]+) contributions?\b", value.strip())
            if match:
                self.cells[self.tooltip]["count"] = int(match[1].replace(",", ""))

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.tooltip = None


def calendar_data(html):
    parser = Calendar()
    parser.feed(html)
    cells = sorted(parser.cells.values(), key=lambda cell: cell["date"])
    if len(cells) < 300:
        raise ValueError("GitHub did not return a complete public calendar")
    if any(cell["level"] > 0 and cell["count"] == 0 for cell in cells):
        raise ValueError("Contribution counts were missing; keeping existing visuals")
    last_week = max(cell["x"] for cell in cells)
    start_week = last_week - 11
    recent = [{**cell, "x": cell["x"] - start_week} for cell in cells if cell["x"] >= start_week]
    return recent


def stats(cells):
    best = streak = 0
    for cell in cells:
        streak = streak + 1 if cell["count"] else 0
        best = max(best, streak)
    return {
        "contributions": sum(cell["count"] for cell in cells),
        "active_days": sum(cell["count"] > 0 for cell in cells),
        "best_streak": best,
        "from": cells[0]["date"], "through": cells[-1]["date"],
    }


def snake_route():
    # A closed, non-intersecting route. Start in the newest week, then move back.
    route = [(x, 0) for x in range(12)]
    for x in range(11, 0, -1):
        route.extend((x, y) for y in (range(1, 7) if x % 2 else range(6, 0, -1)))
    route.extend((0, y) for y in range(6, 0, -1))
    start = route.index((11, 0))
    return route[start:] + route[:start]


def render(cells, summary, dark, mobile):
    width, height = (480, 520) if mobile else (960, 370)
    gx, gy, sx, sy, size = (42, 118, 34, 37, 25) if mobile else (64, 104, 45, 30, 23)
    bg = "#0d1117" if dark else "#ffffff"
    ink = "#e6edf3" if dark else "#1f2328"
    muted = "#9baabe" if dark else "#59677a"
    empty = "#161f2d" if dark else "#edf1f7"
    edge = "#27374f" if dark else "#d5deeb"
    colors = [empty, "#263657", "#3b5281", "#6889c9", "#9bbbff"] if dark else [empty, "#d4dff6", "#a6bbed", "#7392df", "#496bd4"]
    head_color = "#eef5ff" if dark else "#2448a4"
    route = snake_route()
    position = {point: index for index, point in enumerate(route)}
    count = len(route)
    duration = 20.16
    cells_by_position = {(cell["x"], cell["y"]): cell for cell in cells}
    start_date = date.fromisoformat(summary["from"])
    css = [f"text{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;fill:{ink}}}",
           f".muted{{fill:{muted}}}.tile{{stroke:{edge};stroke-width:1}}",
           f".segment{{animation:travel {duration}s linear infinite}}"]
    points = []
    for index, (x, y) in enumerate(route + [route[0]]):
        points.append(f"{index/count*100:.5f}%{{transform:translate({gx+x*sx}px,{gy+y*sy}px)}}")
    css.append("@keyframes travel{" + "".join(points) + "}")
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
           '<title id="title">Ben’s contribution activity — last 12 weeks</title>',
           f'<desc id="desc">{summary["contributions"]} contributions on {summary["active_days"]} active days. Best streak: {summary["best_streak"]} days. An animated snake travels through the real contribution grid.</desc>',
           f'<rect width="{width}" height="{height}" rx="14" fill="{bg}"/>',
           '<defs><filter id="snake-light" x="-100%" y="-100%" width="300%" height="300%"><feDropShadow dx="0" dy="1" stdDeviation="2" flood-color="#729cff" flood-opacity=".65"/></filter></defs>',
           f'<text x="{32 if mobile else 36}" y="40" font-size="{25 if mobile else 27}" font-weight="650">Contribution activity</text>',
           f'<text x="{32 if mobile else 36}" y="69" font-size="15" class="muted">Last 12 weeks · {start_date.strftime("%d %b")} — {date.fromisoformat(summary["through"]).strftime("%d %b %Y")}</text>']
    # Week labels and weekday markers retain the familiar contribution-calendar layout.
    for x in [0, 3, 6, 9]:
        day = start_date + timedelta(weeks=x)
        svg.append(f'<text x="{gx+x*sx}" y="{gy-17}" font-size="13" class="muted">{day.strftime("%d %b")}</text>')
    for y, label in [(1, "M"), (3, "W"), (5, "F")]:
        svg.append(f'<text x="{gx-23}" y="{gy+y*sy+size*.72}" font-size="12" class="muted">{label}</text>')
    for x in range(12):
        for y in range(7):
            cell = cells_by_position.get((x, y))
            level = cell["level"] if cell else 0
            opacity = ' opacity=".35"' if cell is None else ''
            name = f"d{x}-{y}"
            if level:
                arrival = (position[(x, y)] + .45) / count * 100
                css.append(f".{name}{{animation:{name} {duration}s linear infinite}}@keyframes {name}{{0%,{max(0,arrival-.18):.5f}%{{opacity:1}}{arrival:.5f}%,99.98%{{opacity:.18}}100%{{opacity:1}}}}")
            actual_date = cell["date"] if cell else (start_date + timedelta(weeks=x, days=y)).isoformat()
            title = f'{actual_date}: {cell["count"]} contributions' if cell else f'{actual_date}: not yet recorded'
            px, py = gx+x*sx, gy+y*sy
            svg.append(f'<g class="activity-dot {name}"{opacity}><title>{escape(title)}</title><rect x="{px}" y="{py+2}" width="{size}" height="{size}" rx="5" fill="{edge}"/><rect class="tile" x="{px}" y="{py}" width="{size}" height="{size}" rx="5" fill="{colors[level]}"/>')
            if level:
                svg.append(f'<path d="M{px+5} {py+2.5}h{size-10}" stroke="#dce8ff" stroke-opacity=".22" stroke-linecap="round"/>')
            svg.append('</g>')
    for index in range(6, -1, -1):
        x, y = route[-index % count]
        body_size = size * (1 - index * .055)
        inset = (size-body_size)/2
        delay = -duration + index * duration/count
        color = head_color if index == 0 else ("#9bbbff" if index < 3 else "#6889c9")
        svg.append(f'<g class="segment" style="transform:translate({gx+x*sx}px,{gy+y*sy}px);animation-delay:{delay:.4f}s"><rect x="{inset}" y="{inset}" width="{body_size}" height="{body_size}" rx="{body_size*.32}" fill="{color}" opacity="{1-index*.07}" filter="url(#snake-light)"/>')
        if index == 0:
            # A small face distinguishes the head without adding a second animation.
            eye = "#193052" if dark else "#e8f0ff"
            svg.append(f'<circle cx="{size*.36}" cy="{size*.67}" r="1.5" fill="{eye}"/><circle cx="{size*.69}" cy="{size*.67}" r="1.5" fill="{eye}"/>')
        svg.append('</g>')
    metrics = [("Contributions", str(summary["contributions"])), ("Active days", str(summary["active_days"])), ("Best streak", f'{summary["best_streak"]} days')]
    if mobile:
        for index, (label, value) in enumerate(metrics):
            mx = 34 + index*151
            svg.append(f'<text x="{mx}" y="429" font-size="14" class="muted">{label}</text><text x="{mx}" y="462" font-size="27" font-weight="600">{value}</text>')
        footer_x, footer_y = 34, 500
    else:
        for index, (label, value) in enumerate(metrics):
            my = 118 + index*69
            svg.append(f'<text x="704" y="{my}" font-size="15" class="muted">{label}</text><text x="704" y="{my+31}" font-size="27" font-weight="600">{value}</text>')
        footer_x, footer_y = 36, 348
    svg.append(f'<text x="{footer_x}" y="{footer_y}" font-size="13" class="muted">Public GitHub contributions · refreshed daily</text>')
    css.append('@media(prefers-reduced-motion:reduce){.segment,.activity-dot{animation:none!important}}')
    svg.insert(3, '<style>' + ''.join(css) + '</style>')
    svg.append('</svg>')
    return ''.join(svg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', required=True)
    parser.add_argument('--out', default='assets')
    parser.add_argument('--calendar-file')
    parser.add_argument('--stats-only', action='store_true')
    parser.add_argument('--readme', default='README.md')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9-]+', args.user):
        raise ValueError('Invalid GitHub username')
    if args.calendar_file:
        html = Path(args.calendar_file).read_text()
    else:
        request = Request(f'https://github.com/users/{args.user}/contributions', headers={'User-Agent': 'GitHub-profile-activity', 'Accept-Language': 'en-US'})
        for attempt in range(3):
            try:
                with urlopen(request, timeout=30) as response:
                    html = response.read().decode('utf-8')
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
    cells = calendar_data(html)
    summary = stats(cells)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.stats_only:
        readme = Path(args.readme)
        block = ('<!-- activity-stats:start -->\n'
                 '<p align="center"><b>{contributions}</b> contributions · '
                 '<b>{active_days}</b> active days · <b>{best_streak} days</b> best streak'
                 '<br/><sub>Last 12 weeks</sub></p>\n<!-- activity-stats:end -->').format(**summary)
        updated, changed = re.subn(r'<!-- activity-stats:start -->.*?<!-- activity-stats:end -->', lambda match: block, readme.read_text(), flags=re.S)
        if changed != 1:
            raise ValueError('Expected exactly one stats block; refusing to rewrite README')
        readme.write_text(updated)
    else:
        for dark in [True, False]:
            for mobile in [False, True]:
                name = 'activity-' + ('dark' if dark else 'light') + ('-mobile' if mobile else '') + '.svg'
                (out/name).write_text(render(cells, summary, dark, mobile))
    (out/'activity-data.json').write_text(json.dumps({'user': args.user, 'source': f'https://github.com/users/{args.user}/contributions', **summary, 'days': cells}, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
