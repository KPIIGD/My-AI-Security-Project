"""
PPTX 디자인 통일 — 폰트만 일괄 변경, 컨텐츠/색상/레이아웃 불변.
"""
import os, re, shutil, tempfile, zipfile
from pathlib import Path

SRC = r"c:\litellm\capstone_pii_presentation.pptx"
DST = r"c:\litellm\capstone_pii_presentation_polished.pptx"

FONT_KR = "맑은 고딕"
FONT_LATIN = "맑은 고딕"

tmp = Path(tempfile.mkdtemp(prefix="pptx_polish_"))
with zipfile.ZipFile(SRC, "r") as z:
    z.extractall(tmp)

changed_files = 0

def rewrite(path: Path, mutate):
    global changed_files
    text = path.read_text(encoding="utf-8")
    new = mutate(text)
    if new != text:
        path.write_text(new, encoding="utf-8")
        changed_files += 1

def fix_slide(text: str) -> str:
    text = re.sub(r'typeface="[^"]+"', f'typeface="{FONT_KR}"', text)
    return text

def fix_theme(text: str) -> str:
    def sub_scheme(m):
        block = m.group(0)
        block = re.sub(r'<a:latin[^/]*/>', f'<a:latin typeface="{FONT_LATIN}"/>', block)
        block = re.sub(r'<a:ea[^/]*/>', f'<a:ea typeface="{FONT_KR}"/>', block)
        block = re.sub(r'<a:cs[^/]*/>', f'<a:cs typeface="{FONT_KR}"/>', block)
        return block
    text = re.sub(r'<a:majorFont>.*?</a:majorFont>', sub_scheme, text, flags=re.DOTALL)
    text = re.sub(r'<a:minorFont>.*?</a:minorFont>', sub_scheme, text, flags=re.DOTALL)
    text = re.sub(r'typeface="[^"]+"', f'typeface="{FONT_KR}"', text)
    return text

for p in (tmp / "ppt" / "slides").glob("slide*.xml"):
    rewrite(p, fix_slide)

for p in (tmp / "ppt" / "slideLayouts").glob("slideLayout*.xml"):
    rewrite(p, fix_slide)

for p in (tmp / "ppt" / "slideMasters").glob("slideMaster*.xml"):
    rewrite(p, fix_slide)

for p in (tmp / "ppt" / "theme").glob("theme*.xml"):
    rewrite(p, fix_theme)

if Path(DST).exists():
    os.remove(DST)

with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as zout:
    for root, _dirs, files in os.walk(tmp):
        for f in files:
            full = Path(root, f)
            rel = full.relative_to(tmp).as_posix()
            zout.write(full, rel)

shutil.rmtree(tmp, ignore_errors=True)

src_mb = os.path.getsize(SRC) / 1024 / 1024
dst_mb = os.path.getsize(DST) / 1024 / 1024
print(f"[OK] changed_files={changed_files}")
print(f"[OK] SRC: {src_mb:.1f} MB")
print(f"[OK] DST: {dst_mb:.1f} MB -> {DST}")
