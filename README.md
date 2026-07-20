# Aditya Patel — Portfolio

Personal portfolio site. Pure HTML/CSS/JS — no build step, no dependencies.

## Run locally

```bash
cd Portfolio
python3 -m http.server 4173
# open http://localhost:4173
```

(Or just double-click `index.html`.)

## Deploy to GitHub Pages

```bash
cd Portfolio
git init && git add . && git commit -m "Portfolio site"
gh repo create adipatel399.github.io --public --source=. --push
```

The site will be live at **https://adipatel399.github.io** within a minute or two.
(Any repo name works too — enable Pages in repo Settings → Pages → deploy from `main`.)
