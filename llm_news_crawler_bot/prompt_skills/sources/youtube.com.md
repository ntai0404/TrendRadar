# Source Skill: YouTube

Use this skill for `youtube.com`.

## Navigation

- Search-result requests should use YouTube results pages and then open each selected video/channel detail page.
- Correct obvious typos in names only when the intended entity is clear, but preserve the user's query intent.

## Target Selection

- Video targets must be `/watch?v=...` URLs.
- Channel/profile targets are `/@handle`, `/channel/...`, or `/c/...`.
- Do not choose homepage, sidebar, playlist, ad, login, or unrelated recommendation links unless explicitly requested.
- If the user asks for music videos/MVs, prefer official video/watch results and avoid Shorts unless explicitly requested.

## Extraction

- Extract title, channel/author, upload date if visible, description/visible details, tags/keywords when supported by page text.
