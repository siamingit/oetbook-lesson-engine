// Prepare a lesson package for the site's own player, exactly as the site's server does for a draft
// (apps/web/src/server/session-drafts.ts): every section cut and sanitised (cutSection), the stylesheet
// scoped (scopeLessonStylesheet), the session's detail from the bundle.
//   node prep.ts <package folder> <out folder>
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { cutSection, practiceMarks, scopeLessonStylesheet } from "../../../packages/lesson-player/src/section/index.ts";

const [pkg, out] = process.argv.slice(2);
const bundle = JSON.parse(readFileSync(join(pkg, "bundle.json"), "utf8"));
const manifest = JSON.parse(readFileSync(join(pkg, "manifest.json"), "utf8"));
mkdirSync(join(out, "sections"), { recursive: true });
const id = bundle.lesson?.id ?? manifest.lesson_id ?? manifest.id;
const dropped: string[] = [];
const audio: Record<string, string> = {};
for (const s of bundle.sections) {
  const r = cutSection(bundle, s.id, { sessionId: id, packageVersion: 1 });
  if (!r) throw new Error("no section " + s.id);
  for (const [clip, file] of r.audio) audio[clip] = file;
  for (const [block, names] of r.dropped) dropped.push(`${s.id} ${block}: ${names.join(", ")}`);
  writeFileSync(join(out, "sections", s.id + ".json"), JSON.stringify(r.content));
}
const session = {
  id, packageVersion: 1, title: bundle.lesson?.title ?? id, shortTitle: bundle.lesson?.short_title ?? id,
  description: null, durationS: bundle.meta.total_duration_s, playable: true,
  sections: bundle.sections.map((s: any) => ({ id: s.id, title: s.title, intro: !!s.intro, startS: s.start, endS: s.end })),
  practice: practiceMarks(bundle),
};
writeFileSync(join(out, "session.json"), JSON.stringify(session));
writeFileSync(join(out, "audio.json"), JSON.stringify(audio));
writeFileSync(join(out, "lesson.css"), scopeLessonStylesheet(readFileSync(join(pkg, "blocks.css"), "utf8")));
console.log(`${bundle.sections.length} sections; sanitiser removed: ${dropped.length ? dropped.join(" | ") : "nothing"}`);
