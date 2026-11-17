#!/usr/bin/env python3
"""Builds two static book sites (flipbook + standard view) modelled on the
Tamil Arts Academy VTK book layout. Usage: python3 -I build.py"""
import json, html, os, re, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
LAL = os.path.join(ROOT, "..", "data", "lalitha_names.json")
COMPILER = "Compiled and edited by Hrishi"

esc = lambda s: html.escape(s or "", quote=False)
DEV = "०१२३४५६७८९"
def dev(n): return "".join(DEV[int(c)] for c in str(n))
def clean(s): return re.sub(r"^\s*[•\-]\s*", "", s or "").strip()

# ---------------------------------------------------------------- data
def lalitha_book():
    d = json.load(open(LAL, encoding="utf8"))
    chapters = []
    for g in range(10):
        a, b = g * 100 + 1, g * 100 + 100
        parts = []
        for x in d[a - 1:b]:
            h = [f'<section class="nama" id="n{x["number"]}"><header><span class="no">Nāma {x["number"]}</span>'
                 f'<h3 class="sk">{esc(x["name"])}</h3></header>']
            if x["samasa"]:
                h.append('<h4>Samāsa-vigraha</h4>' + "".join(f'<p class="sk-line">{esc(clean(l))}</p>' for l in x["samasa"]))
            if x["wordByWord"]:
                h.append('<h4>Word by word</h4>' + "".join(f'<p>{esc(clean(l))}</p>' for l in x["wordByWord"]))
            if x["summary"]:
                h.append('<h4>Meaning</h4>' + "".join(f'<p>{esc(l)}</p>' for l in x["summary"]))
            if x["esoteric"]:
                h.append('<h4>Esoteric note</h4>' + "".join(f'<p class="eso">{esc(l)}</p>' for l in x["esoteric"]))
            h.append("</section>")
            parts.append("".join(h))
        chapters.append(dict(
            slug=f"chapter_{g+1:02d}", label=f"Section {g+1}", title=f"Names {a}–{b}",
            sub=f"नामानि {dev(a)}–{dev(b)}", html="".join(parts)))
    groups = {}
    for x in sorted(d, key=lambda x: x["name"]):
        groups.setdefault(x["name"][0], []).append(x)
    idx = []
    for ch, items in groups.items():
        idx.append(f'<h4 class="ixh sk">{esc(ch)}</h4>')
        for x in items:
            g = (x["number"] - 1) // 100 + 1
            idx.append(f'<a class="ix" data-go="n{x["number"]}" href="chapter_{g:02d}.html#n{x["number"]}"><span class="ixn">{x["number"]}</span>'
                       f'<span class="sk">{esc(x["name"])}</span><span class="ixp" data-pg="n{x["number"]}"></span></a>')
    back = [dict(slug="index_of_names", label="", title="Index of Names",
                 html='<p class="note">Names in Sanskrit alphabetical order. Select a name to go to its page.</p>' + "".join(idx))]
    front = [
        dict(slug="title", label="", title="Title Page", html=(
            '<div class="titlepage"><p class="sk big">श्रीललितासहस्रनाम</p><h2>Śrī Lalitā Sahasranāma</h2>'
            '<p>The Thousand Names of the Divine Mother</p><p class="small">Samāsa-vigraha, word-by-word meanings,<br>summary and esoteric notes</p>'
            '</div>')),
        dict(slug="about", label="", title="About this Edition", html=(
            '<p>This edition presents all 1000 names of the Lalitā Sahasranāma. For every name it gives the Sanskrit name, '
            'the <i>samāsa-vigraha</i> (grammatical analysis of the compound), word-by-word meanings, a summary of the meaning, '
            'and an esoteric note based on the commentary <i>Saubhāgya-bhāskara</i> of Bhāskararāya.</p>'
            '<p>The names are arranged in ten sections of one hundred names each. Use the Contents button to jump to a section, '
            'the page box to jump to a page, and A− / A+ to change the size of the text.</p>')),
    ]
    return dict(id="lalitha", title="Śrī Lalitā Sahasranāma", short="Lalitā Sahasranāma",
                sk="श्रीललितासहस्रनाम", tag="Samāsa-vigraha, meanings and commentary",
                author="After Bhāskararāya", compiler=COMPILER, accent="#8e1b5a", accent2="#d7a84c",
                front=front, chapters=chapters, back=back)

EN_DURGA = {
    1: "Slaying of Madhu and Kaiṭabha", 2: "Slaying of Mahiṣāsura's Army", 3: "Slaying of Mahiṣāsura",
    4: "Hymn of Śakra and the Devas", 5: "Dialogue of the Devī with the Messenger",
    6: "Slaying of Dhūmralocana", 7: "Slaying of Caṇḍa and Muṇḍa", 8: "Slaying of Raktabīja",
    9: "Slaying of Niśumbha", 10: "Slaying of Śumbha", 11: "Hymn to Nārāyaṇī",
    12: "The Greatness of the Devī and its Fruits", 13: "Boons to Suratha and the Vaiśya"}

def durga_book():
    raw = json.load(open(os.path.join(ROOT, "durga.json"), encoding="utf8"))
    by = {}
    for c in raw:
        ph = sum("awaiting proofread" in v["translation"] for v in c["verses"])
        # prefer the copy of a chapter that has real meanings; keep subtitle from any copy
        cur = by.get(c["id"])
        if cur is None or ph < cur["_ph"]:
            sub = c.get("subtitle") or (cur or {}).get("subtitle")
            by[c["id"]] = dict(c, _ph=ph, subtitle=sub)
        elif not cur.get("subtitle"):
            cur["subtitle"] = c.get("subtitle")
    chapters = []
    for i in range(1, 14):
        c = by[i]
        has = c["_ph"] < len(c["verses"])
        parts = []
        if not has:
            parts.append('<p class="note">Translation and word-by-word meanings for this chapter are in preparation. The Sanskrit text is given below.</p>')
        for v in c["verses"]:
            sk = "<br>".join(esc(l) for l in v["devanagari"].split("\n"))
            h = [f'<section class="verse" id="c{i}v{v["id"]}"><p class="vno">{i}.{v["id"]}</p><p class="sk-verse">{sk}</p>']
            real = "awaiting proofread" not in v["translation"]
            if real:
                h.append(f'<p class="tr">{esc(v["translation"])}</p>')
                rows = [w for w in v["words"] if "awaiting proofread" not in w["meaning"]]
                if rows:
                    h.append('<table class="wbw">' + "".join(
                        f'<tr><td class="w">{esc(w["word"])}</td><td>{esc(w["meaning"])}</td></tr>' for w in rows) + "</table>")
            h.append("</section>")
            parts.append("".join(h))
        sub = (c.get("subtitle") or "")
        chapters.append(dict(slug=f"chapter_{i:02d}", label=f"Chapter {i}", title=EN_DURGA[i],
                             sub=re.sub(r"^[०-९0-9]+\.\s*", "", sub), html="".join(parts)))
    front = [
        dict(slug="title", label="", title="Title Page", html=(
            '<div class="titlepage"><p class="sk big">श्रीदुर्गासप्तशती</p><h2>Śrī Durgā Saptaśatī</h2>'
            '<p>Devī Māhātmya in Thirteen Chapters</p><p class="small">Sanskrit text with translation and word-by-word meanings</p>'
            '</div>')),
        dict(slug="about", label="", title="About this Edition", html=(
            '<p>This edition presents the thirteen chapters of the Durgā Saptaśatī (Devī Māhātmya) in Devanagari, '
            'following the Gītā Press verse numbering.</p>'
            '<p>An English translation and word-by-word meaning are given verse by verse wherever they have been prepared. '
            'At present these are complete for Chapter 6; the remaining chapters carry the Sanskrit text, and their meanings will be added as they are proofread.</p>'
            '<p>Use the Contents button to jump to a chapter, the Index of Verses at the end to jump to any verse, the page box to jump to a page, and A− / A+ to change the size of the text.</p>')),
    ]
    idx=[]
    for ci,c in enumerate(chapters,1):
        n=len(by[ci]["verses"])
        idx.append(f'<h4 class="ixh">Chapter {ci}. {esc(EN_DURGA[ci])}</h4><div class="ixg">')
        for v in by[ci]["verses"]:
            vid=f'c{ci}v{v["id"]}'
            idx.append(f'<a class="ix ixv" data-go="{vid}" href="chapter_{ci:02d}.html#{vid}"><span class="ixn">{ci}.{v["id"]}</span><span class="ixp" data-pg="{vid}"></span></a>')
        idx.append('</div>')
    back=[dict(slug="index_of_verses", label="", title="Index of Verses",
               html='<p class="note">Every verse by chapter and number, with its page. Select a verse to go to it.</p>'+"".join(idx))]
    return dict(id="durga", back=back, title="Śrī Durgā Saptaśatī", short="Durgā Saptaśatī",
                sk="श्रीदुर्गासप्तशती", tag="Devī Māhātmya — text and meanings",
                author="Mārkaṇḍeya Purāṇa", compiler=COMPILER, accent="#6e1d35", accent2="#d7a84c",
                front=front, chapters=chapters)

# ---------------------------------------------------------------- templates

def lalitha_cover(b):
    import base64
    from PIL import Image
    fn="ambika.jpg" if b["id"]=="lalitha" else "durga_cover.jpg"
    img=base64.b64encode(open(os.path.join(ROOT,fn),"rb").read()).decode()
    iw,ih=Image.open(os.path.join(ROOT,fn)).size
    pw=340; ph=round(pw*ih/iw); px=(600-pw)//2; py=52
    credit = '' if b["id"]=="lalitha" else '<text x="300" y="762" text-anchor="middle" font-size="10" fill="#35607f" font-family="Georgia,serif">Picture: Wellcome Collection, CC BY 4.0</text>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 600 800">
<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a9dcf3"/><stop offset="1" stop-color="#e6f6fd"/></linearGradient></defs>
<rect width="600" height="800" fill="url(#sky)"/><rect x="22" y="22" width="556" height="756" fill="none" stroke="#1f4e79" stroke-width="2.5"/>
<rect x="32" y="32" width="536" height="736" fill="none" stroke="#d29a2a" stroke-width="1"/>
<rect x="{px-8}" y="{py-8}" width="{pw+16}" height="{ph+16}" fill="#d29a2a"/><rect x="{px-4}" y="{py-4}" width="{pw+8}" height="{ph+8}" fill="#fff8e6"/>
<image x="{px}" y="{py}" width="{pw}" height="{ph}" preserveAspectRatio="xMidYMid slice" xlink:href="data:image/jpeg;base64,{img}"/>
<text x="300" y="{py+ph+62}" text-anchor="middle" font-size="50" fill="#7a1535" font-family="'Noto Serif Devanagari','Kohinoor Devanagari','Devanagari Sangam MN',serif">{b["sk"]}</text>
<text x="300" y="{py+ph+106}" text-anchor="middle" font-size="28" fill="#1f3a5f" font-family="Georgia,serif">{esc(b["title"])}</text>
<text x="300" y="{py+ph+140}" text-anchor="middle" font-size="16" fill="#35607f" font-family="Georgia,serif" font-style="italic">{esc(b["tag"])}</text>{credit}</svg>"""

def render_cover(o):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--disable-gpu"])
        pg=br.new_page(viewport={"width":900,"height":1200},device_scale_factor=1.5)
        open(f"{o}/_c.html","w").write('<body style="margin:0"><img id=i src="cover.svg" style="width:900px;height:1200px;display:block"></body>')
        pg.goto("file://"+os.path.abspath(o)+"/_c.html")
        pg.wait_for_function("document.getElementById('i').complete"); pg.wait_for_timeout(500)
        pg.screenshot(path=f"{o}/cover.png",clip={"x":0,"y":0,"width":900,"height":1200}); br.close()
    os.remove(f"{o}/_c.html")
    from PIL import Image
    Image.open(f"{o}/cover.png").convert("RGB").save(f"{o}/cover.jpg",quality=90); os.remove(f"{o}/cover.png")

def cover_svg(b):
    if b['id'] in ('lalitha','durga'): return lalitha_cover(b)
    a, g = b["accent"], b["accent2"]
    petals = "".join(f'<ellipse cx="300" cy="190" rx="14" ry="46" transform="rotate({k*22.5} 300 300)" fill="none" stroke="{g}" stroke-width="1.4"/>' for k in range(16))
    petals2 = "".join(f'<ellipse cx="300" cy="228" rx="10" ry="30" transform="rotate({k*30+15} 300 300)" fill="{g}" fill-opacity=".18" stroke="{g}" stroke-width="1"/>' for k in range(12))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800">
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="#2a0a14"/></linearGradient></defs>
<rect width="600" height="800" fill="url(#bg)"/><rect x="24" y="24" width="552" height="752" fill="none" stroke="{g}" stroke-width="2"/>
<rect x="34" y="34" width="532" height="732" fill="none" stroke="{g}" stroke-width=".8"/>
<g>{petals}{petals2}<circle cx="300" cy="300" r="150" fill="none" stroke="{g}" stroke-width="1.2"/>
<circle cx="300" cy="300" r="118" fill="none" stroke="{g}" stroke-width=".8"/><circle cx="300" cy="300" r="10" fill="{g}"/></g>
<text x="300" y="545" text-anchor="middle" font-size="54" fill="{g}" font-family="'Noto Serif Devanagari','Kohinoor Devanagari','Devanagari Sangam MN',serif">{b["sk"]}</text>
<text x="300" y="600" text-anchor="middle" font-size="30" fill="#fff" font-family="Georgia,serif">{esc(b["title"])}</text>
<text x="300" y="646" text-anchor="middle" font-size="17" fill="{g}" font-family="Georgia,serif" font-style="italic">{esc(b["tag"])}</text>
</svg>'''

CSS = """
:root{--accent:%(accent)s;--gold:%(accent2)s;--paper:#dccfb0;--ink:#2a2218;--fs:18px}
*{box-sizing:border-box}html,body{margin:0;height:100%%}:root{--st:env(safe-area-inset-top,0px);--sb:env(safe-area-inset-bottom,0px)}
body{font-family:'Noto Serif','Georgia','Times New Roman',serif;color:var(--ink);background:#2a1a14}
.sk,.sk-line,.sk-verse,.w{font-family:'Noto Serif Devanagari','Kohinoor Devanagari','Devanagari Sangam MN','Sanskrit Text','Mangal',serif}
.book h1{font-size:1.9em;color:var(--accent);margin:.2em 0 .1em;text-align:center}
.book .sub{text-align:center;color:#6a4a22;margin:0 0 1em;font-style:italic}
.book .label{text-align:center;letter-spacing:.2em;text-transform:uppercase;font-size:.7em;color:#8a4a10;margin-top:0}
.book h2{color:var(--accent);font-size:1.5em;text-align:center}
.book h3{margin:.2em 0}.book h4{margin:.9em 0 .25em;color:var(--accent);font-size:.8em;letter-spacing:.12em;text-transform:uppercase;break-after:avoid}
.book p{margin:0 0 .6em;line-height:1.6;hyphens:auto}
.nama{border-top:1px solid #a98a52;padding-top:.8em;margin-top:1em}
.nama header{break-after:avoid}.no{color:#8a4a10;font-weight:700;font-size:.8em;letter-spacing:.1em}
.nama .sk{font-size:1.9em;color:var(--accent);font-weight:600}
.sk-line{font-size:1.1em;margin:.1em 0}.eso{font-size:.95em;color:#3b2410}
.verse{break-inside:avoid;margin:0 0 1.1em;padding-bottom:.6em;border-bottom:1px dotted #a98a52}
.vno{color:#8a4a10;font-weight:700;font-size:.75em;margin:0 0 .2em!important;letter-spacing:.1em}
.sk-verse{font-size:1.35em;line-height:1.75!important;color:#3a0f1c;margin:0 0 .5em!important}
.tr{font-style:italic}.note{font-size:.9em;color:#6a4a22;border-left:3px solid var(--gold);padding-left:.7em}
.wbw{border-collapse:collapse;width:100%%;font-size:.85em;margin:.3em 0}.wbw td{padding:.15em .4em;vertical-align:top;border-bottom:1px solid #c9ad74}.wbw .w{width:38%%;color:var(--accent)}
.titlepage{text-align:center;padding-top:18%%}.titlepage .big{font-size:2.6em;color:var(--accent);margin:0}.titlepage .small{font-size:.85em;color:#6a4a22}
.cover{margin:0;height:100%%;break-after:column}.cover svg{width:100%%;height:100%%;display:block}
.chap-head{break-before:column;padding-top:12%%}.front-head{break-before:column}
.blank{break-after:column;height:100%%}
.ix{display:flex;gap:.6em;align-items:baseline;color:inherit;text-decoration:none;padding:.2em .2em;border-bottom:1px dotted #a98a52;break-inside:avoid}
.ixg{display:flex;flex-wrap:wrap;gap:.15em .5em;margin-bottom:.8em}.ix.ixv{width:6.2em;padding:.15em .3em;flex:none;gap:.4em}.ix.ixv .ixn{width:auto;font-size:.85em}.ixh{margin:.8em 0 .3em;color:var(--accent);font-size:1em}.ix:hover{background:rgba(160,120,50,.18)}.ix .ixn{width:2.8em;color:#8a4a10;font-size:.8em}.ix .sk{flex:1;font-size:1.15em}.ix .ixp{font-size:.8em;color:#6a4a22}
.ixh{font-size:1.5em!important;margin:.8em 0 .2em!important;border-bottom:2px solid #a98a52;break-after:avoid;letter-spacing:0!important;text-transform:none!important}
"""

FLIP_CSS = """
.lf-layer{position:absolute;inset:0;perspective:4200px;pointer-events:none;z-index:6}
.lf-half,.lf-leaf{position:absolute;top:0;bottom:0;width:50%%}
.lf-half{overflow:hidden}.lf-leaf{transform-style:preserve-3d;will-change:transform}
.lf-face{position:absolute;inset:0;overflow:hidden;backface-visibility:hidden;-webkit-backface-visibility:hidden}
.lf-vp{position:absolute;overflow:hidden}.lf-shade{position:absolute;inset:0;background:#2a1a08;opacity:0}
.pgR,.pgL{background-color:#dccfb0}
.pgR{background-image:linear-gradient(90deg,rgba(110,85,45,.28),rgba(110,85,45,0) 14%%),url("data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260'%%3E%%3Cfilter id='n'%%3E%%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%%3E%%3CfeColorMatrix values='0 0 0 0 .42 0 0 0 0 .32 0 0 0 0 .16 0 0 0 .30 0'/%%3E%%3C/filter%%3E%%3Crect width='100%%25' height='100%%25' filter='url(%%23n)'/%%3E%%3C/svg%%3E"),radial-gradient(ellipse at 40%% 35%%,rgba(255,250,230,.55),rgba(255,250,230,0) 65%%)}
.pgL{background-image:linear-gradient(270deg,rgba(110,85,45,.28),rgba(110,85,45,0) 14%%),url("data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260'%%3E%%3Cfilter id='n'%%3E%%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%%3E%%3CfeColorMatrix values='0 0 0 0 .42 0 0 0 0 .32 0 0 0 0 .16 0 0 0 .30 0'/%%3E%%3C/filter%%3E%%3Crect width='100%%25' height='100%%25' filter='url(%%23n)'/%%3E%%3C/svg%%3E"),radial-gradient(ellipse at 40%% 35%%,rgba(255,250,230,.55),rgba(255,250,230,0) 65%%)}

body.flip{overflow:hidden}
.topbar{position:fixed;top:0;left:0;right:0;height:calc(48px + var(--st));padding-top:var(--st);box-sizing:border-box;background:#1c0f0a;color:#f1dfb8;display:flex;align-items:center;gap:14px;padding:0 14px;z-index:20;font-family:system-ui,sans-serif;font-size:15px}
.topbar b{font-family:Georgia,serif;font-size:17px}.topbar span{opacity:.7}.topbar a{margin-left:auto;color:var(--gold);text-decoration:none;border:1px solid var(--gold);border-radius:8px;padding:5px 10px}
.btn{background:#3a2218;color:#f1dfb8;border:1px solid #6b4a36;border-radius:8px;padding:6px 11px;font-size:14px;cursor:pointer;font-family:system-ui,sans-serif}.btn:hover{background:#4d2e20}
.controls{position:fixed;bottom:0;left:0;right:0;height:calc(52px + var(--sb));padding-bottom:var(--sb);box-sizing:border-box;background:#1c0f0a;display:flex;gap:8px;align-items:center;justify-content:center;z-index:20;color:#f1dfb8;font-family:system-ui,sans-serif;font-size:14px;flex-wrap:wrap}
.controls input{width:64px;padding:5px;border-radius:6px;border:1px solid #6b4a36;background:#2a1a14;color:#f1dfb8}
.splash{position:fixed;top:calc(48px + var(--st));bottom:calc(52px + var(--sb));left:0;right:0;display:flex;align-items:center;justify-content:center;z-index:4}.splash img{height:min(88%%,680px);box-shadow:0 10px 30px rgba(70,45,15,.45)}.splash{display:none!important}body.ready .splash{display:none}body.flip:not(.go) #flow>*:not(#blank):not(#cover){display:none}body.flip:not(.ready) .controls,body.flip:not(.ready) .arrow,body.flip:not(.ready) .topbar{pointer-events:none}.stage{position:fixed;top:calc(48px + var(--st));bottom:calc(52px + var(--sb));left:0;right:0;display:flex;align-items:center;justify-content:center;perspective:2200px;background-color:#d3b47a;background-image:url("data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260'%%3E%%3Cfilter id='n'%%3E%%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%%3E%%3CfeColorMatrix values='0 0 0 0 .42 0 0 0 0 .32 0 0 0 0 .16 0 0 0 .30 0'/%%3E%%3C/filter%%3E%%3Crect width='100%%25' height='100%%25' filter='url(%%23n)'/%%3E%%3C/svg%%3E"),radial-gradient(circle at 50%% 30%%,rgba(255,235,190,.35),rgba(120,80,30,.25))}
.book{flex:none;transition:transform .2s;position:relative;background-color:#dccfb0;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 .42 0 0 0 0 .32 0 0 0 0 .16 0 0 0 .30 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"),radial-gradient(ellipse at 40% 35%,rgba(255,250,230,.55),rgba(255,250,230,0) 65%),radial-gradient(ellipse at 70% 80%,rgba(150,120,70,.18),rgba(150,120,70,0) 60%),linear-gradient(90deg,rgba(110,85,45,.22),rgba(110,85,45,0) 6%,rgba(110,85,45,0) 94%,rgba(110,85,45,.22));box-shadow:0 10px 30px rgba(70,45,15,.45),0 0 0 1px rgba(120,95,55,.35);border-radius:3px;font-size:var(--fs)}
.book:after{content:"";position:absolute;top:0;bottom:0;left:50%%;width:34px;margin-left:-17px;background:linear-gradient(90deg,#0000,#0002 45%%,#0003 50%%,#0002 55%%,#0000);pointer-events:none}
.book.single:after{display:none}
.viewport{position:absolute;inset:34px 38px;overflow:hidden}
#flow{height:100%%;column-fill:auto}
.arrow{position:fixed;top:50%%;transform:translateY(-50%%);z-index:15;font-size:28px;background:#0007;color:#f1dfb8;border:0;border-radius:50%%;width:44px;height:44px;cursor:pointer}
.arrow.l{left:10px}.arrow.r{right:10px}
.turn{animation:turn .25s ease}@keyframes turn{0%%{opacity:.85}100%%{opacity:1}}
#toc{position:fixed;top:calc(48px + var(--st));left:0;bottom:calc(52px + var(--sb));width:min(340px,86vw);background:#1c0f0aee;color:#f1dfb8;z-index:30;transform:translateX(-102%%);transition:transform .25s;overflow:auto;padding:14px;font-family:system-ui,sans-serif}
#toc.open{transform:none}#toc a{display:flex;justify-content:space-between;gap:10px;color:#f1dfb8;text-decoration:none;padding:9px 6px;border-bottom:1px solid #3a2218;cursor:pointer}#toc a:hover{background:#3a2218}
"""

STD_CSS = """
body.std{background-color:#d3b47a;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 .42 0 0 0 0 .32 0 0 0 0 .16 0 0 0 .30 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");color:var(--ink);font-family:'Noto Serif',Georgia,serif;margin:0;font-size:18px}
.std header.site{background:var(--accent);color:#fff;padding:18px 20px;text-align:center}.std header.site a{color:#fff;text-decoration:none}
.std header.site h1{margin:0;font-size:1.4em;color:#fff}.std header.site p{margin:.2em 0 0;color:#f1dfb8;font-size:.85em}
.std nav.top{display:flex;gap:10px;justify-content:center;padding:10px;flex-wrap:wrap;font-family:system-ui,sans-serif;font-size:14px}
.std nav.top a,.std nav.pn a{color:var(--accent);text-decoration:none;border:1px solid var(--accent);border-radius:8px;padding:6px 12px;background:#fff8}
.std main{max-width:760px;margin:0 auto;padding:10px 20px 40px;background-color:#dccfb0;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 .42 0 0 0 0 .32 0 0 0 0 .16 0 0 0 .30 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"),radial-gradient(ellipse at 40% 35%,rgba(255,250,230,.55),rgba(255,250,230,0) 65%),radial-gradient(ellipse at 70% 80%,rgba(150,120,70,.18),rgba(150,120,70,0) 60%),linear-gradient(90deg,rgba(110,85,45,.22),rgba(110,85,45,0) 6%,rgba(110,85,45,0) 94%,rgba(110,85,45,.22));box-shadow:0 0 30px #0002}
.std nav.pn{display:flex;justify-content:space-between;gap:10px;padding:14px 0;font-family:system-ui,sans-serif;font-size:14px}
.std .toc{list-style:none;padding:0}.std .toc li{padding:10px 4px;border-bottom:1px solid #e0d2b0;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.std .toc a{color:var(--accent);text-decoration:none;font-weight:600}.std .toc .sk{display:block;font-size:.9em;color:#6a4a22;font-weight:400}.std .toc .fl{font-family:system-ui,sans-serif;font-size:13px}
.std .cov{display:block;max-width:300px;margin:18px auto;box-shadow:0 8px 24px #0004}
@media print{.std header.site,.std nav{display:none}.std main{box-shadow:none;max-width:none}.nama,.verse{break-inside:avoid}}
"""

FONTS_CSS = open(os.path.join(ROOT, 'fonts', 'fonts_local.css'), encoding='utf8').read()

def page_head(b, title, extra_css=""):
    css = (CSS % b) + extra_css.replace("%%", "%")
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="theme-color" content="#1c0f0a"><link rel="manifest" href="manifest.webmanifest"><link rel="apple-touch-icon" href="icon-180.png">'
            f'<title>{esc(title)}</title>'
            f'<style>{FONTS_CSS}</style><style>{css}</style></head>')

def chapter_block(ch, flip=False):
    cls = "chap-head" if flip else ""
    return (f'<div class="{cls}" id="{ch["slug"]}">' + (f'<p class="label">{esc(ch["label"])}</p>' if ch["label"] else "") +
            f'<h1>{esc(ch["title"])}</h1>' + (f'<p class="sub sk">{esc(ch["sub"])}</p>' if ch.get("sub") else "") + '</div>' + ch["html"])

def build_flip(b):
    toc_items = [(c["slug"], c["title"]) for c in b["front"]] + [(c["slug"], (c["label"] + ". " if c["label"] else "") + c["title"]) for c in b["chapters"]] + [(c["slug"], c["title"]) for c in b.get("back", [])]
    body = ['<div class="blank" id="blank"></div><div class="cover" id="cover"><img alt="Cover" src="cover.jpg" decoding="sync" style="width:100%;height:100%;display:block"></div>']
    for c in b["front"]:
        body.append(f'<div class="front-head" id="{c["slug"]}"><h1>{esc(c["title"])}</h1></div>' if c["slug"] != "title" else f'<div class="front-head" id="title"></div>')
        body.append(c["html"])
    for c in b["chapters"]:
        body.append(chapter_block(c, True))
    for c in b.get("back", []):
        body.append(f'<div class="front-head" id="{c["slug"]}"><h1>{esc(c["title"])}</h1></div>')
        body.append(c["html"])
    toc = "".join(f'<a data-go="{s}"><span>{esc(t)}</span><span data-pg="{s}"></span></a>' for s, t in toc_items)
    js = open(os.path.join(ROOT, "flip.js"), encoding="utf8").read()
    return (page_head(b, b["title"], FLIP_CSS) + f'<body class="flip"><div class="splash" id="splash"><img src="cover.jpg" alt=""></div><div class="topbar"><button class="btn" id="menu">☰</button><b>{esc(b["title"])}</b>'
            f'<span>{esc(b["author"])}</span><a href="contents.html">Standard View</a></div>'
            f'<div id="toc">{toc}</div><button class="arrow l" id="prev2" aria-label="Previous">‹</button><button class="arrow r" id="next2" aria-label="Next">›</button>'
            f'<div class="stage"><div class="book" id="book"><div class="viewport"><div id="flow">{"".join(body)}</div></div></div></div>'
            '<div class="controls"><button class="btn" id="first">⏮</button><button class="btn" id="prev">◀ Prev</button>'
            '<span id="pg">Page 1</span><button class="btn" id="next">Next ▶</button><button class="btn" id="contents">📑 Contents</button>'
            '<input id="gopage" type="number" min="1" placeholder="Page"><button class="btn" id="go">Go</button>'
            '<button class="btn" id="smaller">A−</button><span id="zoom">100%</span><button class="btn" id="larger">A+</button><button class="btn" id="fs" style="display:none">⛶ Full screen</button></div>'
            f'<script>{js}</script></body></html>')

def std_page(b, title, inner, prev=None, nxt=None, flip_hash=""):
    nav = '<nav class="pn">' + (f'<a href="{prev[0]}">← {esc(prev[1])}</a>' if prev else "<span></span>") + \
          '<a href="contents.html">Contents</a>' + (f'<a href="{nxt[0]}">{esc(nxt[1])} →</a>' if nxt else "<span></span>") + "</nav>"
    return (page_head(b, f'{title} — {b["title"]}', STD_CSS) + f'<body class="std"><header class="site"><h1><a href="contents.html">{esc(b["title"])}</a></h1><p>{esc(b["author"])}</p></header>'
            f'<nav class="top"><a href="index.html{flip_hash}">Switch to 3D Flipbook View</a><a href="contents.html">Index</a></nav>'
            f'<main class="book">{nav}{inner}{nav}</main></body></html>')

def build_std(b, out):
    seq = [(c["slug"], c["title"] if not c["label"] else f'{c["label"]}. {c["title"]}', c) for c in b["front"] if c["slug"] != "title"] + \
          [(c["slug"], f'{c["label"]}. {c["title"]}', c) for c in b["chapters"]] + [(c["slug"], c["title"], c) for c in b.get("back", [])]
    lis = "".join(f'<li><span><a href="{s}.html">{esc(t)}</a>' + (f'<span class="sk">{esc(c["sub"])}</span>' if c.get("sub") else "") + f'</span>'
                  f'<a class="fl" href="index.html#{s}">flipbook</a></li>' for s, t, c in seq)
    inner = f'<img class="cov" src="cover.jpg" alt="Cover"><h1>Contents</h1><ul class="toc">{lis}</ul>'
    open(f"{out}/contents.html", "w", encoding="utf8").write(std_page(b, "Contents", inner))
    for i, (s, t, c) in enumerate(seq):
        prev = (f"{seq[i-1][0]}.html", seq[i-1][1]) if i else None
        nxt = (f"{seq[i+1][0]}.html", seq[i+1][1]) if i + 1 < len(seq) else None
        inner = chapter_block(c) if c in b["chapters"] else f'<h1>{esc(c["title"])}</h1>' + c["html"]
        open(f"{out}/{s}.html", "w", encoding="utf8").write(std_page(b, t, inner, prev, nxt, f"#{s}"))

def main():
    shutil.rmtree(OUT, ignore_errors=True)
    for b in (lalitha_book(), durga_book()):
        o = f"{OUT}/{b['id']}"; os.makedirs(o)
        open(f"{o}/cover.svg", "w", encoding="utf8").write(cover_svg(b))
        render_cover(o)
        for fn in os.listdir(os.path.join(ROOT, "fonts")):
            if fn.endswith(".woff2"): shutil.copy(os.path.join(ROOT, "fonts", fn), os.path.join(o, fn))
        open(f"{o}/index.html", "w", encoding="utf8").write(build_flip(b))
        build_std(b, o)
        for ic in ("icon-180.png","icon-192.png","icon-512.png"): shutil.copy(os.path.join(ROOT, ic), os.path.join(o, ic))
        open(f"{o}/manifest.webmanifest", "w", encoding="utf8").write(json.dumps({"name":b["title"],"short_name":"Lalitha","start_url":"index.html","scope":".","display":"fullscreen","display_override":["fullscreen","standalone"],"background_color":"#1c0f0a","theme_color":"#1c0f0a","icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png"},{"src":"icon-512.png","sizes":"512x512","type":"image/png"}]}))
        open(f"{o}/.nojekyll", "w").close()
        print(b["id"], len(os.listdir(o)), "files")

main()
