# Aditya Patel — Portfolio

Personal portfolio site. Pure HTML/CSS/JS with no build step. Three.js and Matter.js are bundled locally.

## Run locally

```bash
cd Portfolio
python3 -m http.server 4173
# open http://localhost:4173
```

Use the local server above; the 3D portrait loads ES modules and model assets over HTTP.

## Deploy to GitHub Pages

```bash
cd Portfolio
git init && git add . && git commit -m "Portfolio site"
gh repo create adipatel399.github.io --public --source=. --push
```

The site will be live at **https://adipatel399.github.io** within a minute or two.
(Any repo name works too — enable Pages in repo Settings → Pages → deploy from `main`.)

## Interactive design

- Responsive dropdown navigation on phones and tablets.
- Projects use a sticky section: vertical page scrolling moves the project cards sideways. Arrow buttons and keyboard focus also navigate; reduced motion uses a native horizontal rail.
- Skill balls support pointer dragging on touchscreens and mice, with a reset button. Physics pauses outside the viewport.
- The 3D bust follows pointer/touch position. Three.js and Matter.js are hosted locally, with a portrait fallback if WebGL is unavailable.

## Blender portrait

The portrait is a textured human mesh prepared in Blender, with a light-blue polo,
backward charcoal baseball cap, textured swept hair, smoked sunglasses, and a slight closed-mouth smile.
The upper-body mesh is cropped at the abdomen, with a soft fade at the edge. A weighted
head/neck rig follows mouse and touch input; the whole face and jaw turn together,
with blending confined to the neck. Subtle breathing pauses offscreen.
Curved sunglasses use a locally generated studio reflection environment.
Run `Blender --background --python tools/check-avatar-rig.py` to check facial rigidity.
Reduced motion disables the entrance and idle motion. A rendered WebP portrait
covers loading and WebGL failures.

- Runtime model: `assets/avatar/portrait.glb` (Draco-compressed, about 2.7 MB).
- Editable Blender scene: `tools/portrait.blend`.
- Rebuild: `/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/build-avatar.py`.
- Build inputs: `tools/avatar-source/`. The Blender scene includes the studio lighting.
- The hairstyle follows the supplied reference photo, with short sides and a fuller swept front visible beneath the backward cap. The character remains an interpretation, not a scan.

## Asset credits

Human topology, young male shape targets, skin/eye textures, eyebrows, and the
base garment are adapted from the MakeHuman community's CC0 assets. The cap,
polo collar and placket, glasses, pose adaptation, and web integration are authored for this portfolio.
Source links and licenses are in `assets/avatar/CREDITS.md` and
`tools/avatar-source/LICENSE.ASSETS.md`.

Three.js r170 and Matter.js 0.19.0 are MIT-licensed; Draco is Apache-2.0-licensed.
All runtime code and decoders are served locally from `assets/vendor/`.
