import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = json.loads((ROOT / "results" / "summary.json").read_text())
ASSETS = ROOT / "assets"; ASSETS.mkdir(exist_ok=True)


def chart(path, title, subtitle, labels, values, color):
    w, h, left, top, cw, ch = 1200, 650, 150, 120, 950, 400
    maximum = max(values) * 1.15
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           '<rect width="100%" height="100%" fill="#F8FAFC"/>',
           f'<text x="{left}" y="48" font-family="Arial" font-size="30" font-weight="700" fill="#172B4D">{title}</text>',
           f'<text x="{left}" y="80" font-family="Arial" font-size="16" fill="#5E6C84">{subtitle}</text>']
    gap = cw / len(values); bw = gap * .58
    for i, (label, value) in enumerate(zip(labels, values)):
        x = left + i * gap + (gap-bw)/2; bh = ch*value/maximum; y=top+ch-bh
        out += [f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="5" fill="{color}"/>',
                f'<text x="{x+bw/2}" y="{y-10}" text-anchor="middle" font-family="Arial" font-size="15" font-weight="700">{value}</text>',
                f'<text x="{x+bw/2}" y="{top+ch+30}" text-anchor="middle" font-family="Arial" font-size="14">{label}</text>']
    out.append('</svg>'); path.write_text("\n".join(out))


order = ["success", "failure", "cancelled", "skipped"]
chart(ASSETS / "run_conclusions.svg", "Observed workflow conclusions",
      "300 completed pandas-dev/pandas runs retrieved from the GitHub REST API",
      [x.title() for x in order], [SUMMARY["conclusions"][x] for x in order], "#6554C0")
signatures = SUMMARY["first_failed_step_signatures"][:7]
short = {"Test (not single_cpu)": "Test (parallel)", "Create virtual environment with Pixi": "Create Pixi env",
         "Test pandas for Pyodide": "Test Pyodide"}
chart(ASSETS / "failed_step_signatures.svg", "First failed step in failed jobs",
      "Triage signatures from 181 failed jobs; step names are not root-cause labels",
      [short.get(x[0], x[0]) for x in signatures], [x[1] for x in signatures], "#D64550")
print("created 2 SVG charts")
