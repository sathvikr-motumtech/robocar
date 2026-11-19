# motumtech.in website

This folder is the source for https://motumtech.in. The rest of the `robocar` repo is the project code the posts talk about.

Static site built with [Hugo](https://gohugo.io/) and the [PaperMod](https://github.com/adityatelange/hugo-PaperMod) theme.

## First-time setup on a new machine

```bash
brew install hugo
git clone --recurse-submodules https://github.com/sathvikr-motumtech/robocar.git
cd robocar/website
```

## Everyday workflow

Run these from the `website/` folder.

```bash
hugo new posts/my-new-post/index.md   # create a post (starts as a draft)
hugo server --buildDrafts             # live preview at http://localhost:1313
# edit content/posts/my-new-post/index.md, drop images in the same folder
# set `draft: false` when ready
git add . && git commit -m "Add my new post" && git push   # publishes (once deploy is set up)
```

## Writing

- **Images**: put them next to `index.md` and write `![alt text](photo.png)`.
- **Code**: fenced blocks with a language, e.g. ```` ```python ````.
- **Math**: `$x^2$` inline, `$$ ... $$` on its own lines for display math.
  Write `\$` for a literal dollar sign.
- **Tags / categories / series**: set them in the front matter at the top of the post.
- **Photos**: run `python3 scripts/strip_image_metadata.py` before committing — phone photos
  contain GPS location. Publishing is blocked if any image still has metadata.
- **Drafts**: this repo is public, so anything you push (even `draft: true`) is visible on
  GitHub. Keep unfinished posts uncommitted until they're ready.

## Layout

| Path | What it is |
|------|------------|
| `hugo.yaml` | Site configuration (menus, theme options, permalinks) |
| `content/` | All pages and posts (Markdown) |
| `scripts/` | `strip_image_metadata.py` (privacy), `wp_import.py` (one-time WordPress import) |
| `layouts/` | Small overrides of the theme (math rendering, etc.) |
| `static/` | Files copied as-is (KaTeX stylesheet and fonts) |
| `themes/PaperMod/` | The theme (git submodule — don't edit) |
| `private/` | Ignored by git. WordPress export/backups go here — never publish. |
