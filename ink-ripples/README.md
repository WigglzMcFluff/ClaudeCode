# Ink Ripples

An interactive canvas animation: moving your cursor or finger paints flowing,
curl-noise trails, and clicking drops a fading ripple. Built with plain
HTML/CSS/JavaScript — no build step or dependencies.

## Running locally

From this folder, start the included static file server:

```powershell
powershell -ExecutionPolicy Bypass -File serve.ps1
```

Then open http://localhost:8642 in your browser.

(If you're using Claude Code's dev server preview, the `ink-ripples`
configuration in `.claude/launch.json` runs the same script for you.)

## Controls

- **Move cursor / finger** — draw flowing particle trails
- **Click / tap** — drop a ripple
- **Toolbar**
  - Palette swatches — pick a color palette
  - Both / Trails / Ripples — switch which effect is active
  - Fade slider — control how quickly the canvas fades to background
  - Clear — wipe the canvas
