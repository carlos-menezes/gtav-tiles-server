# GTA V Map Tiles

https://github.com/user-attachments/assets/8ef03deb-3607-4976-8477-3ae810d5363d

An interactive slippy map of GTA V's Los Santos, built with [MapLibre GL](https://maplibre.org/).

## Live demo

Hosted on GitHub Pages.

## Reproducing the tiles

[You need a copy of the GTA V webmap image](http://mega.nz/folder/NPV0CR5D#saAobmin1AOjfny8P66Xkw) (e.g. `GTAV_Webmap_Dawn.png`). Then run:

```bash
curl https://raw.githubusercontent.com/jahed/maptiles/refs/heads/master/maptiles | bash -s GTAV_Webmap_Dawn.png tiles
```

This generates the `tiles/{z}/{x}/{y}.png` XYZ tile tree used by the viewer. You should be able to serve the `tiles` directory with any static file server, and point the viewer to it.
