# Book generator

`python3 build.py` builds the Lalitha (and Durga) books into `generator/out/<id>/` from `../data/lalitha_names.json`, `flip.js`, `fonts/`, the cover pictures and icons here. Needs Python 3, Pillow and Playwright (Chromium) for the cover picture.

To publish: copy `out/lalitha/*` into `../book/`, write `../book/manifest.txt` (first line `version <unix time>`, then one file name per line), commit, and push to `main` and `gh-pages`.

The Mac app source is in `../native` (build with `bash build_app.sh`).
