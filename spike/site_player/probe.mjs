// The site's own player (the harness page built by check_site_player.py), driven to given moments in headless Edge
// over CDP: at each, the site guard's verdict on the board (data-oa-fit, data-oa-whole, data-oa-fit-why), every
// line of text on the board measured as check_text_size.py measures the engine's player (its size in the 1600x900
// frame, a hand line at its size / 1.3; its contrast with what is drawn behind it), and a screenshot of the frame.
//   node probe.mjs <page url> <moments.json> <frame width> <out dir> <rules json>
// moments.json: [{"t": seconds, "name": "file stem", "board": id}]; writes <out dir>/probe.json
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const [base, momentsFile, widthArg, outDir, rulesJson] = process.argv.slice(2);
const W = +widthArg;
const R = JSON.parse(rulesJson);
const moments = JSON.parse(fs.readFileSync(momentsFile, "utf8"));
fs.mkdirSync(outDir, { recursive: true });
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const sleep = ms => new Promise(r => setTimeout(r, ms));

const MEASURE = `(() => {
  const R = ${JSON.stringify(R)};
  const frame = document.querySelector('.frame'), cam = document.querySelector('#cam');
  const k = 900 / frame.getBoundingClientRect().height;
  const body = cam.parentElement, br = body.getBoundingClientRect();
  const A = { left: br.left, top: br.top, right: br.right, bottom: br.bottom };
  const scaleOf = el => { let e = el; while (e && !(e.offsetWidth > 0)) e = e.parentElement; return e ? e.getBoundingClientRect().width / e.offsetWidth : 1; };
  const rgba = s => { const m = s.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; const p = m[1].split(/[ ,\\/]+/).filter(Boolean).map(parseFloat); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const over = (c, b, a) => [0, 1, 2].map(i => c[i] * a + b[i] * (1 - a));
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const drawn = (el, color) => {
    const chain = []; for (let e = el; e && e !== document.documentElement; e = e.parentElement) { chain.unshift(e); if (e === frame) break; }
    let behind = [255, 255, 255]; const layers = [];
    for (const e of chain) { const cs = getComputedStyle(e); const b = rgba(cs.backgroundColor); const before = behind;
      if (b && b[3] > 0) behind = over(b, behind, b[3]);
      const g = cs.backgroundImage.match(/^linear-gradient\\((rgba?\\([^)]*\\)), (rgba?\\([^)]*\\))\\)$/);
      if (g && g[1] === g[2]) { const w = rgba(g[1]); if (w[3] > 0) behind = over(w, behind, w[3]); }
      layers.push({ before, op: parseFloat(cs.opacity) }); }
    const c = rgba(color); let fg = over(c, behind, c[3]), bg = behind, op = 1;
    for (let i = layers.length - 1; i >= 0; i--) { const L = layers[i]; if (L.op < 1) { fg = over(fg, L.before, L.op); bg = over(bg, L.before, L.op); } op *= L.op; }
    return { fg, bg, op, alpha: c[3] };
  };
  const words = s => s.trim().split(/\\s+/).filter(Boolean).length;
  const pieceOf = el => { for (let e = el; e && e !== cam; e = e.parentElement) { const d = getComputedStyle(e).display; if (d !== 'inline' && d !== 'contents') return e; } return el; };
  const isHand = cs => /caveat|ink free|segoe print|bradley hand|chalkboard|cursive/i.test(cs.fontFamily.split(',')[0]);
  const found = []; let minRun = 99, minLabel = 99;
  for (const el of cam.querySelectorAll(':scope > .blk')) {
    if (!(el.classList.contains('on') || el.dataset.oaLayer === 'fixed')) continue;
    if (getComputedStyle(el).display === 'none') continue;
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n; (n = walker.nextNode());) {
      if (!n.data.trim()) continue;
      const p = n.parentElement, cs = getComputedStyle(p);
      if (cs.visibility === 'hidden') continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      if (![...rg.getClientRects()].some(q => q.width > 0 && q.right > A.left && q.left < A.right && q.bottom > A.top && q.top < A.bottom)) continue;
      const d = drawn(p, cs.color); if (d.alpha === 0 || d.op < 0.02) continue;
      const piece = pieceOf(p);
      const label = piece.tagName === 'TH' || !!p.closest('th') || cs.textTransform === 'uppercase' || words(piece.innerText || piece.textContent) <= R.words;
      const px = parseFloat(cs.fontSize) * scaleOf(p) * k, eq = isHand(cs) ? px / R.hand : px;
      if (label) minLabel = Math.min(minLabel, eq); else minRun = Math.min(minRun, eq);
      const text = n.data.trim().slice(0, 48);
      if (eq < (label ? R.label : R.run) - R.tol) found.push({ kind: label ? 'small label' : 'small text', block: el.dataset.id, text, value: +eq.toFixed(1) });
      const c = ratio(d.fg, d.bg);
      if (c < R.contrast) found.push({ kind: 'low contrast', block: el.dataset.id, text, value: +c.toFixed(2) });
    }
  }
  return { fit: cam.dataset.oaFit || '', whole: cam.dataset.oaWhole || null, why: cam.dataset.oaFitWhy || '',
           title: (frame.querySelector('.hdr .t') || {}).textContent || '', minRun: +minRun.toFixed(1), minLabel: +minLabel.toFixed(1),
           frame: [Math.round(frame.getBoundingClientRect().width), Math.round(frame.getBoundingClientRect().height)], found };
})()`;

// One browser per moment: in one long session the player was left waiting on "Loading" for a later section.
async function browser() {
  const prof = fs.mkdtempSync(path.join(os.tmpdir(), "oet-site-"));
  const port = 9700 + Math.floor(Math.random() * 250);
  const edge = spawn(EDGE, ["--headless=new", "--do-not-de-elevate", "--disable-gpu", "--mute-audio", `--remote-debugging-port=${port}`,
    `--user-data-dir=${prof}`, `--window-size=${W + 40},${Math.round(W * 9 / 16) + 400}`, "about:blank"], { stdio: "ignore" });
  let ws;
  for (let i = 0; i < 80; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); const p = l.find(x => x.type === "page");
      if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); break; } } catch (e) { /* not up yet */ }
    await sleep(250);
  }
  await new Promise(r => ws.addEventListener("open", r, { once: true }));
  let id = 0; const pending = new Map();
  ws.addEventListener("message", ev => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async e => { const r = await send("Runtime.evaluate", { expression: e, awaitPromise: true, returnByValue: true });
    if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0, 400)); return r.result?.result?.value; };
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: W + 40, height: Math.round(W * 9 / 16) + 400, deviceScaleFactor: 1, mobile: false });
  const close = async () => { ws.close(); edge.kill(); await sleep(400); try { fs.rmSync(prof, { recursive: true, force: true }); } catch (e) { /* locked */ } };
  return { send, ev, close };
}

const out = [];
for (const m of moments) {
  const { send, ev, close } = await browser();
  const url = `${base}?t=${m.t}`;
  await send("Page.navigate", { url });
  for (let i = 0; i < 160; i++) {
    if (await ev(`location.href === ${JSON.stringify(url)} && document.readyState === 'complete' && !!document.querySelector('.frame #cam .blk')`)) break;
    await sleep(150);
  }
  await ev(`(async()=>{ document.documentElement.style.setProperty('--harness-w','${W}px'); if (document.fonts) await document.fonts.ready; return true })()`);
  let loading = true;
  for (let i = 0; i < 100 && loading; i++) {   // the section's content loaded (the player's "Loading…" notice gone)
    loading = await ev(`/Loading/.test(document.body.innerText || '')`);
    if (loading) await sleep(200);
  }
  await sleep(1600);                         // the board's entrance and the guard settle
  const res = await ev(MEASURE);
  res.loading = await ev(`/Loading/.test(document.body.innerText || '')`);
  const r = await ev(`(()=>{ const b=document.querySelector('.frame').getBoundingClientRect(); return [b.left,b.top,b.width,b.height]; })()`);
  const shot = await send("Page.captureScreenshot", { format: "png", clip: { x: r[0], y: r[1], width: r[2], height: r[3], scale: 1 } });
  fs.writeFileSync(path.join(outDir, m.name + ".png"), Buffer.from(shot.result.data, "base64"));
  out.push({ ...m, ...res });
  process.stdout.write(`${m.name} ${m.board || ""} fit=${res.fit || "-"} whole=${res.whole ?? "-"} loading=${res.loading} min ${res.minRun}/${res.minLabel} findings ${res.found.length}\n`);
  await close();
}
fs.writeFileSync(path.join(outDir, "probe.json"), JSON.stringify(out, null, 1));
