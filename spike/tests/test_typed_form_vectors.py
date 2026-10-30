"""The reference player's typed marker against the site's test vectors for oet-typed-form-v1
(contracts 1.13.0, `test-vectors/oet-typed-form-v1.json`; site #201: "Please run your reference
player against those vectors"). The player's own functions (ppNorm, ppExpand, ppTyped) are taken
from the template's text and run in node. Skipped where node or the pinned contracts are missing
(CI: the contracts repository is private)."""

import json
import shutil
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lesson_package as lp  # noqa: E402

TEMPLATE = Path(__file__).resolve().parents[1] / "scripts" / "board_player_template.html"
RUN = r"""
const fs = require("fs");
const src = fs.readFileSync(process.argv[1], "utf8");
const grab = (name) => {
  const rest = src.slice(src.indexOf(name));
  const m = /\n(?=function |const |\/\/ )/.exec(rest.slice(1));
  return rest.slice(0, m ? m.index + 1 : rest.length);
};
const api = new Function([grab("const PP_NUM"), grab("function ppNorm("), grab("function ppExpand("),
                          grab("function ppTyped(")].join("\n") + "\nreturn { ppNorm, ppTyped };")();
const d = JSON.parse(fs.readFileSync(0, "utf8"));
const out = d.vectors.map(v => ({ case: v.case, right: api.ppTyped({ scoring: { accepted: v.accepted,
  marking_scheme: d.scheme }, feedback: { key: "", wrong_answers: [] } }, v.response).right,
  norm: api.ppNorm(v.response, d.scheme) }));
console.log(JSON.stringify(out));
"""


def vectors() -> bytes | None:
    try:
        path = lp.cache_dir() / lp.lock()["asset"]
        if not path.exists() or lp.sha256_file(path) != lp.lock()["sha256"]:
            return None
        with zipfile.ZipFile(path) as z:
            return z.read("test-vectors/oet-typed-form-v1.json")
    except (OSError, KeyError):
        return None


class TypedFormVectors(unittest.TestCase):
    def test_the_player_passes_every_vector(self):
        raw, node = vectors(), shutil.which("node")
        if raw is None or node is None:
            self.skipTest("node or the pinned contracts are not available")
        d = json.loads(raw)
        got = json.loads(subprocess.run([node, "-e", RUN, str(TEMPLATE)], input=raw, capture_output=True,
                                        check=True).stdout)
        self.assertEqual(len(got), len(d["vectors"]))
        for v, g in zip(d["vectors"], got):
            with self.subTest(case=v["case"]):
                self.assertEqual(g["right"], v["right"])
                if "normalised_response" in v:
                    self.assertEqual(g["norm"], v["normalised_response"])


if __name__ == "__main__":
    unittest.main()
