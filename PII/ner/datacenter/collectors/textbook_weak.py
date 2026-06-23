"""Collector (Phase B weak): maywell korean_textbooks — 교육 텍스트 24만 (text)."""
from __future__ import annotations
import glob
from pathlib import Path
from ._text_weak import weak_label_texts
_DIR = Path(__file__).resolve().parents[2]/"data"/"external"/"huggingface"/"maywell__korean_textbooks"
META={"id":"textbook_weak","kind":"weak_examples","license":"maywell/HF 교과서 (PSEUDO 검수필요)","entities":["NAME","ORG","ADDRESS","DISEASE"],"note":"교육 텍스트 weak"}
_CAP=60000
def collect(limit:int=0)->dict:
    import pyarrow.parquet as pq
    cap=limit or _CAP; texts=[]
    for fp in sorted(glob.glob(str(_DIR/"**"/"*.parquet"),recursive=True)):
        if 'cache' in fp: continue
        t=pq.read_table(fp,columns=["text"])
        for v in t.column("text").to_pylist():
            if v: texts.append(str(v)[:8000])
            if len(texts)>=cap: break
        if len(texts)>=cap: break
    return {"kind":"weak_examples","license":META["license"],"examples":weak_label_texts(texts,min_len=40)}
