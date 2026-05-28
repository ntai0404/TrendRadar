# Source Skill: Facebook

Use this skill for `facebook.com`.

## Session

- Prefer an existing or auto-created Chrome CDP profile. Do not rely on headless username/password login unless no CDP session exists.
- If the page is a login, checkpoint, QR-login, recovery, or identify page, do not pretend it is the requested post/group content.

## Target Selection

- Group/page post targets should be `/posts/` or `/permalink/` URLs.
- Do not select login, recovery, identify, about, group root, profile root, marketplace, or notification URLs as post items.
- Return fewer clean post URLs instead of padding with unrelated Facebook links.

## Extraction

- Extract visible post text, author/page/group name, timestamp if visible, media caption if visible, and engagement only if directly visible.
