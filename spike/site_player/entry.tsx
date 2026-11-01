// The site's own lesson player (packages/lesson-player/web), mounted with a lesson prepared by prep.ts, at the
// moment given in the address (?t=seconds), paused. For screenshots of the site's rendering.
import "@oetacademy/lesson-player/web/player.css";
import { LessonPlayer } from "@oetacademy/lesson-player/web";
import { createRoot } from "react-dom/client";

const q = new URLSearchParams(location.search);
const t = Number(q.get("t") || 0);
(async () => {
  const session = await (await fetch("out/session.json")).json();
  const audio: Record<string, string> = await (await fetch("out/audio.json")).json();
  const root = createRoot(document.getElementById("root")!);
  root.render(
    <LessonPlayer
      session={session}
      learnerCode="TEST-0000"
      startAt={t}
      loadSection={async (id) => (await fetch(`out/sections/${id}.json`)).json()}
      grantMedia={async (r) => ({
        clips: r.utterances.filter((u) => audio[u]).map((u) => ({ utterance: u, url: "pkg/" + audio[u], expiresAt: "2099-01-01T00:00:00Z" })),
        images: [],
      })}
    />,
  );
  (window as any).__harnessReady = true;
})();
