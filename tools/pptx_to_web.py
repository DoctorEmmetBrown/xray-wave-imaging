#!/usr/bin/env python3
"""
Turn a PowerPoint course into a web slide deck that keeps its animations.

    python3 tools/pptx_to_web.py path/to/course.pptx reconstruction-tomographique

Writes
    static/courses/<slug>/slides/NN.webp      one image per slide (and per click step)
    static/courses/<slug>/anim/*.webm|.mp4     every animated GIF, as a looping video
    static/courses/<slug>/<slug>.pdf          a PDF copy to download
    data/courses/<slug>.yaml                  the slide list read by the viewer

What "keeps the animations" means here
    * Animated GIFs play: each one is converted to a short looping video (WebM and
      MP4, a tenth of the size of the GIF) and laid exactly over its place on the
      slide, crop included.
    * Click-by-click entrances ("Appear", "Fade"... on whole shapes) become extra
      steps: the slide is shown first without the shapes, then with them, in
      click order — exactly what the right arrow does in PowerPoint.
    * Morph, motion paths, emphasis effects and transitions are not reproduced;
      the slide shows its final state.

Needs LibreOffice (soffice), pdftoppm (poppler), ffmpeg and Pillow.
Run it where those are installed; then commit the two output folders.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
WIDTH = 1920          # rendered slide width in pixels
QUALITY = 82          # webp quality

NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"


def sh(*cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def to_pdf(pptx: Path, outdir: Path) -> Path:
    sh("soffice", "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(pptx))
    return outdir / (pptx.stem + ".pdf")


def render_page(pdf: Path, page: int, out: Path):
    tmp = out.with_suffix("")
    sh("pdftoppm", "-png", "-f", str(page), "-l", str(page), "-scale-to-x", str(WIDTH),
       "-scale-to-y", "-1", "-singlefile", str(pdf), str(tmp))
    Image.open(str(tmp) + ".png").convert("RGB").save(out, "WEBP", quality=QUALITY, method=6)
    Path(str(tmp) + ".png").unlink()


def slide_order(z: zipfile.ZipFile):
    """Slide XML paths in presentation order."""
    pres = z.read("ppt/presentation.xml").decode("utf8")
    rels = z.read("ppt/_rels/presentation.xml.rels").decode("utf8")
    target = dict(re.findall(r'Id="(rId\d+)"[^>]*?Target="(slides/slide\d+\.xml)"', rels))
    target.update({a: b for b, a in re.findall(r'Target="(slides/slide\d+\.xml)"[^>]*?Id="(rId\d+)"', rels)})
    ids = re.findall(r'<p:sldId [^>]*r:id="(rId\d+)"', pres)
    size = re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"', pres)
    return ["ppt/" + target[i] for i in ids], int(size.group(1)), int(size.group(2))


def gif_overlays(z, slide_path, cx, cy):
    """Position (in % of the slide) and crop of every GIF picture on a slide."""
    rel_path = slide_path.replace("slides/", "slides/_rels/") + ".rels"
    rels = z.read(rel_path).decode("utf8")
    gifs = dict(re.findall(r'Id="(rId\d+)"[^>]*?Target="\.\./media/([^"]+\.gif)"', rels))
    gifs.update({a: b for b, a in re.findall(r'Target="\.\./media/([^"]+\.gif)"[^>]*?Id="(rId\d+)"', rels)})
    if not gifs:
        return []
    xml = z.read(slide_path).decode("utf8")
    out = []
    for pic in re.findall(r"<p:pic>.*?</p:pic>", xml, re.S):
        rid = re.search(r'r:embed="(rId\d+)"', pic)
        if not rid or rid.group(1) not in gifs:
            continue
        start = xml.find(pic)
        if xml.rfind("<p:grpSp>", 0, start) > xml.rfind("</p:grpSp>", 0, start):
            print(f"  ! {gifs[rid.group(1)]} on {slide_path} sits inside a group — position may be off")
        x, y = map(int, re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"', pic).groups())
        w, h = map(int, re.search(r'<a:ext cx="(\d+)" cy="(\d+)"', pic).groups())
        crop = {k: 0.0 for k in "ltrb"}
        src = re.search(r"<a:srcRect([^/]*)/>", pic)
        if src:
            for k, v in re.findall(r'([ltrb])="(-?\d+)"', src.group(1)):
                crop[k] = int(v) / 100000
        out.append({
            "gif": gifs[rid.group(1)],
            "left": round(100 * x / cx, 3), "top": round(100 * y / cy, 3),
            "width": round(100 * w / cx, 3), "height": round(100 * h / cy, 3),
            "crop": {k: round(v * 100, 3) for k, v in crop.items()},
        })
    return out


def click_entrances(xml):
    """Shape ids revealed by successive clicks (entrance effects only)."""
    timing = re.search(r"<p:timing>.*</p:timing>", xml, re.S)
    if not timing:
        return []
    steps = []
    # each click is a <p:par> whose effect nodes carry nodeType="clickEffect"
    for block in re.split(r'(?=<p:cTn [^>]*nodeType="clickEffect")', timing.group(0))[1:]:
        if 'presetClass="entr"' not in block[:400]:
            continue
        ids = re.findall(r'<p:spTgt spid="(\d+)"', block)
        if ids:
            steps.append(ids[0])
    return steps


def remove_shapes(xml, ids):
    """Drop the top-level shapes (sp, pic, grpSp, graphicFrame) with these ids."""
    for sid in ids:
        for tag in ("p:grpSp", "p:sp", "p:pic", "p:graphicFrame", "p:cxnSp"):
            pat = re.compile(rf"<{tag}>(?:(?!<{tag}>).)*?<p:cNvPr id=\"{sid}\".*?</{tag}>", re.S)
            new, n = pat.subn("", xml, count=1)
            if n:
                xml = new
                break
    return xml


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pptx, slug = Path(sys.argv[1]).resolve(), sys.argv[2]
    out = ROOT / "static" / "courses" / slug
    if out.exists():
        shutil.rmtree(out)
    (out / "slides").mkdir(parents=True)
    (out / "anim").mkdir()

    with tempfile.TemporaryDirectory() as tmpd:
        tmp = Path(tmpd)
        z = zipfile.ZipFile(pptx)
        slides, cx, cy = slide_order(z)

        print("rendering the deck…")
        pdf = to_pdf(pptx, tmp)
        shutil.copy(pdf, out / f"{slug}.pdf")

        deck, gif_done = [], {}
        for n, sp in enumerate(slides, start=1):
            xml = z.read(sp).decode("utf8")
            entry = {"slide": n, "img": f"slides/{n:02d}.webp"}
            render_page(pdf, n, out / entry["img"])

            # animated GIFs → looping videos (WebM for Chrome/Firefox, MP4 for Safari),
            # positioned over the slide
            vids = []
            for o in gif_overlays(z, sp, cx, cy):
                g = o.pop("gif")
                if g not in gif_done:
                    stem = f"anim/{Path(g).stem}"
                    (tmp / g).write_bytes(z.read(f"ppt/media/{g}"))
                    even = "scale=trunc(iw/2)*2:trunc(ih/2)*2"
                    sh("ffmpeg", "-y", "-i", str(tmp / g), "-an", "-vf", even, "-pix_fmt", "yuv420p",
                       "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "36", "-row-mt", "1", str(out / f"{stem}.webm"))
                    sh("ffmpeg", "-y", "-i", str(tmp / g), "-an", "-vf", even, "-pix_fmt", "yuv420p",
                       "-movflags", "+faststart", "-c:v", "libx264", "-crf", "23", "-preset", "slow",
                       str(out / f"{stem}.mp4"))
                    gif_done[g] = stem
                vids.append({"src": gif_done[g], **o})
            if vids:
                entry["videos"] = vids

            # click entrances → extra steps rendered without the shapes still to come
            clicks = click_entrances(xml)
            if clicks:
                steps = []
                for k in range(len(clicks)):
                    hidden = clicks[k:]
                    variant = tmp / f"step-{n}-{k}.pptx"
                    with zipfile.ZipFile(pptx) as src, zipfile.ZipFile(variant, "w", zipfile.ZIP_DEFLATED) as dst:
                        for item in src.infolist():
                            data = src.read(item.filename)
                            if item.filename == sp:
                                data = remove_shapes(data.decode("utf8"), hidden).encode("utf8")
                            dst.writestr(item, data)
                    vdir = tmp / f"v{n}-{k}"
                    vdir.mkdir()
                    vpdf = to_pdf(variant, vdir)
                    img = f"slides/{n:02d}-{k}.webp"
                    render_page(vpdf, n, out / img)
                    steps.append(img)
                entry["steps"] = steps      # shown before the final image, in order
            deck.append(entry)
            print(f"  slide {n:2d}" + (f"  · {len(vids)} animation(s)" if vids else "")
                  + (f"  · {len(clicks)} click step(s)" if clicks else ""))

    data = ROOT / "data" / "courses"
    data.mkdir(parents=True, exist_ok=True)
    with open(data / f"{slug}.yaml", "w") as f:
        f.write(f"# Generated by tools/pptx_to_web.py from {pptx.name} — do not edit by hand.\n")
        yaml.safe_dump({"ratio": round(cx / cy, 5), "pdf": f"{slug}.pdf", "slides": deck},
                       f, sort_keys=False, allow_unicode=True)
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"done: {len(deck)} slides, {len(gif_done)} animations, {size/1e6:.1f} MB in static/courses/{slug}/")


if __name__ == "__main__":
    main()
