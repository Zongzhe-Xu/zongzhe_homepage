# Zongzhe Xu — Personal Homepage

A lightweight, static academic homepage (plain HTML + CSS + a little vanilla JS, no build step).
The background is a procedurally painted watercolour of a coastline seen from above (`tools/paint_coast.py`):
sand and a frothy shoreline under the hero, shallows below, deepening to navy where the text turns white.

```bash
python3 tools/paint_coast.py /tmp/coast   # writes sea.jpg and sand.png; convert to WebP into images/
```

## Structure

```
zongzhe_homepage/
├── index.html      # Page content — edit here
├── style.css       # "Painted Coast" theme
├── .nojekyll       # Tells GitHub Pages to serve files as-is
├── images/
│   ├── sea.webp    # painted sea backdrop (generated)
│   ├── sand.webp   # painted beach + shoreline (generated)
│   ├── profile.png
│   ├── inertia1.png
│   ├── sleeplm.png
│   ├── this_time_is_different.png
│   └── sfm.png
├── cv/
│   └── Zongzhe_Xu_CV.pdf
├── tools/
│   └── paint_coast.py  # regenerates sea.jpg + sand.png (needs numpy, Pillow)
└── README.md
```

## Preview locally

```bash
cd zongzhe_homepage
python3 -m http.server 8000
# open http://localhost:8000
```

## Deploy to GitHub Pages

The simplest path is a user site at `https://<username>.github.io`.

1. Create a **public** repo named exactly `<your-github-username>.github.io`
   (e.g., `zongzhex.github.io`).
2. From inside this `zongzhe_homepage/` folder:

   ```bash
   git init
   git add .
   git commit -m "Initial homepage"
   git branch -M main
   git remote add origin git@github.com:<your-github-username>/<your-github-username>.github.io.git
   git push -u origin main
   ```
3. In the repo settings on GitHub → **Pages**, confirm the source is the
   `main` branch, root (`/`). The `.nojekyll` file ensures everything is served
   as static HTML.
4. Your site will be live at `https://<your-github-username>.github.io` within
   a minute or two.

If instead you want a project site at `https://<username>.github.io/homepage/`,
name the repo whatever you like (e.g., `homepage`) and enable Pages from the
repo settings the same way.

## Making updates

After deploying, any future edits just need:

```bash
git add .
git commit -m "Update homepage"
git push
```

GitHub Pages will rebuild automatically.
