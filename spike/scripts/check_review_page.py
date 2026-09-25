"""Check that every audio element on a review page loads, as opened from disk.

    .venv/Scripts/python spike/scripts/check_review_page.py <page.html>

The page is copied beside itself with a small harness added, opened from its
file:// URL in headless Edge with the sound muted, and read back with
--dump-dom (the same method as check_marks.py). The harness loads every
<audio> and records, per element, its duration or its error code. Nothing is
played aloud and nothing is paid for.

Exit code 0 only when the page has at least one audio element and every one
loaded with a duration; otherwise each failure is printed and the exit code is
non-zero. Run it on every review page before handing it over.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]

HARNESS = """
<script>
(function () {
  const els = Array.from(document.querySelectorAll('audio'));
  const out = els.map(a => ({src: a.getAttribute('src'), ok: false, duration: null, error: null}));
  let left = els.length;
  const done = () => {
    const pre = document.createElement('pre');
    pre.id = 'audio-result';
    pre.textContent = JSON.stringify(out);
    document.body.appendChild(pre);
  };
  if (!left) return done();
  const settle = (i, f) => { if (out[i].settled) return; out[i].settled = true; f(); if (--left === 0) done(); };
  els.forEach((a, i) => {
    a.muted = true;
    a.addEventListener('loadedmetadata', () => settle(i, () => {
      out[i].duration = a.duration; out[i].ok = a.duration > 0;
    }));
    a.addEventListener('error', () => settle(i, () => {
      out[i].error = a.error ? a.error.code + ' ' + (a.error.message || '') : 'error';
    }));
    a.preload = 'auto';
    a.load();
  });
})();
</script>
"""


def check(page: Path) -> list[dict]:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        raise SystemExit("Edge not found; the review page check needs a browser")
    harness = page.with_name(page.stem + "_audio_check.html")
    html = page.read_text(encoding="utf-8")
    harness.write_text(html.replace("</body>", HARNESS + "</body>") if "</body>" in html
                       else html + HARNESS, encoding="utf-8")
    try:
        r = subprocess.run([edge, "--headless=new", "--disable-gpu", "--mute-audio",
                            "--virtual-time-budget=15000", "--dump-dom",
                            harness.resolve().as_uri()], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
    finally:
        harness.unlink(missing_ok=True)
    m = re.search(r'<pre id="audio-result">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit("the harness produced no result: some audio never loaded or failed "
                         "within the time budget, or the page did not run")
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")
                      .replace("&lt;", "<").replace("&gt;", ">"))


def main() -> None:
    page = Path(sys.argv[1])
    results = check(page)
    bad = [x for x in results if not x["ok"]]
    for x in results:
        state = f"ok {x['duration']:.1f} s" if x["ok"] else f"FAILED ({x['error'] or 'no duration'})"
        print(f"  {state:<22} {x['src']}")
    print(f"{len(results)} audio elements, {len(results) - len(bad)} loaded, {len(bad)} failed")
    if not results or bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
