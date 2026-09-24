# spike/superseded/

The slide-based path, replaced by the board model (docs/00-PRODUCT.md §2,
methodology §18). Moved here on 2026-09-24 so they are not run by mistake.
They import from `spike/scripts/` and will not run from this folder without
being moved back; that is deliberate.

| Script | Replaced by |
|---|---|
| `write_script.py` | `write_narration.py` |
| `qa_script.py` | `qa_narration.py` (its model, rates and checks are now held there) |
| `build_timeline.py` | `build_board_timeline.py` |
| `build_bundle.py` | `build_board_bundle.py` |
| `build_player.py`, `player_template.html` | `build_board_player.py`, `build_lesson_player.py`, `board_player_template.html` |
| `check_page.py` | `check_board_page.py` |
| `playthrough.py` | `check_board_page.py` and `check_marks.py` (deterministic; no real-time playback) |
