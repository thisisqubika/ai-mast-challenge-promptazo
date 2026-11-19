# Background music for the AI Recap video

One track per recap tone. The slides video (`POST /events/{id}/recap/slides-video`)
uses the file matching the chosen tone; if it's missing, the video has no music.

| Tone (UI)  | File name (any of .mp3 / .m4a / .wav) |
|------------|---------------------------------------|
| Exciting   | `emocionante.mp3`                     |
| Inspiring  | `inspirador.mp3`                      |
| Humorous   | `humoristico.mp3`                     |
| Nostalgic  | `nostalgico.mp3`                      |

The track is trimmed (or looped) to the video length, with a short fade in/out.

Use royalty-free music only (e.g. Pixabay Music — no attribution required — or
Kevin MacLeod / incompetech.com — CC BY 4.0, credit required).
Record each track's source and license below.

| File | Title / Author | Source URL | License |
|------|----------------|------------|---------|
| `emocionante.mp3` | "Volatile Reaction" — Kevin MacLeod | https://incompetech.com/music/royalty-free/mp3-royaltyfree/Volatile%20Reaction.mp3 | CC BY 4.0 |
| `inspirador.mp3` | "Inspired" — Kevin MacLeod | https://incompetech.com/music/royalty-free/mp3-royaltyfree/Inspired.mp3 | CC BY 4.0 |
| `humoristico.mp3` | "Monkeys Spinning Monkeys" — Kevin MacLeod | https://incompetech.com/music/royalty-free/mp3-royaltyfree/Monkeys%20Spinning%20Monkeys.mp3 | CC BY 4.0 |
| `nostalgico.mp3` | "Dreamer" — Kevin MacLeod | https://incompetech.com/music/royalty-free/mp3-royaltyfree/Dreamer.mp3 | CC BY 4.0 |

Changes: each track was trimmed to its first 60 seconds (with a fade-out) and
re-encoded at 128 kbps to keep the repo small.

**Required credit (CC BY 4.0)** — include it wherever the video is published
(e.g. the post description):

> Music by Kevin MacLeod (incompetech.com), licensed under Creative Commons:
> By Attribution 4.0 — http://creativecommons.org/licenses/by/4.0/
