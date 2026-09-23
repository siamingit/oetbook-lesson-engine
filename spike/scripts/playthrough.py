"""Play one built page through from start to finish in a real browser.

    .venv/Scripts/python spike/scripts/playthrough.py <lesson_dir> <page>

Normally reached via check_page.py --playthrough. Off by default: it costs a
lesson-length of wall clock and stalls intermittently under muted headless
playback, so a stalled run needs a re-run before it means anything.

Serves the generated page over http://localhost so media loads normally,
opens it in headless Edge with autoplay allowed, presses play once, and then
touches nothing. The page reports which utterance is on screen as it goes;
if audio ever stalls, the lesson clock stalls with it (audio is the clock),
so a frozen time is a failure and is reported as one.
"""

import http.server
import json
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

LESSON = Path(sys.argv[1])
PAGE = int(sys.argv[2])
PAGE_DIR = LESSON / "generated" / f"page-{PAGE}"
PORT = 8137
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
RESULT_PATH = Path(__file__).with_name("playthrough_result.json")

HARNESS = """
<script>
window.addEventListener("load", function () {
  var log = [];
  var lastSubtitle = null;
  var lastTime = null;
  var lastTimeChangeAt = Date.now();
  var startedAt = Date.now();
  var done = false;

  function report(status) {
    if (done) return;
    done = true;
    var body = JSON.stringify({
      status: status,
      seconds_elapsed: (Date.now() - startedAt) / 1000,
      final_time: document.getElementById("timeLabel").textContent,
      entries: log
    });
    fetch("/log", { method: "POST", body: body });
  }

  play();

  setInterval(function () {
    if (done) return;
    var label = document.getElementById("timeLabel").textContent;
    var sub = document.getElementById("subtitle").textContent.slice(0, 60);
    if (sub && sub !== lastSubtitle) {
      lastSubtitle = sub;
      log.push({ at: label, text: sub });
    }
    if (label !== lastTime) {
      lastTime = label;
      lastTimeChangeAt = Date.now();
    } else if (Date.now() - lastTimeChangeAt > 30000) {
      report("STALLED");
    }
    var playing = document.getElementById("playPause").getAttribute("aria-label") === "Pause";
    if (!playing && (Date.now() - startedAt) > 5000) {
      report("FINISHED");
    }
  }, 250);
});
</script>
"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PAGE_DIR), **kwargs)

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        payload = self.rfile.read(length)
        RESULT_PATH.write_bytes(payload)
        self.send_response(204)
        self.end_headers()
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *args):
        pass


def main() -> None:
    harness_path = PAGE_DIR / "player_verify.html"
    html = (PAGE_DIR / "player.html").read_text(encoding="utf-8")
    harness_path.write_text(html.replace("</body>", HARNESS + "</body>"), encoding="utf-8")

    if RESULT_PATH.exists():
        RESULT_PATH.unlink()

    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("127.0.0.1", PORT), Handler)

    browser = subprocess.Popen([
        EDGE,
        "--headless=new",
        "--disable-gpu",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        # Decodes and plays normally -- `ended` still fires and timing is still
        # real -- but routes nothing to the machine's speakers.
        "--mute-audio",
        "--user-data-dir=" + str(Path(__file__).with_name("edge_profile")),
        f"http://127.0.0.1:{PORT}/player_verify.html",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    deadline = time.time() + 15 * 60
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    while thread.is_alive() and time.time() < deadline:
        time.sleep(1)
    server.shutdown()
    browser.terminate()
    harness_path.unlink(missing_ok=True)

    if not RESULT_PATH.exists():
        print("NO RESULT: browser never reported back")
        sys.exit(1)

    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    print("status:", result["status"])
    print("wall seconds:", round(result["seconds_elapsed"], 1))
    print("final time label:", result["final_time"])
    print("distinct subtitles seen:", len(result["entries"]))


if __name__ == "__main__":
    main()
