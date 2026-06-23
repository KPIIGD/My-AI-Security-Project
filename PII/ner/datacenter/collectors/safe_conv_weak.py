"""Collector (Phase B weak): jojo0217 korean_safe_conversation — 대화 (instruction+output)."""
from __future__ import annotations
import glob,json
from pathlib import Path
from ._text_weak import weak_label_texts
_DIR=Path(__file__).resolve().parents[2]/"data"/"external"/"huggingface"/"jojo0217__korean_safe_conversation"
META={"id":"safe_conv_weak","kind":"weak_examples","license":"jojo0217/HF 안전대화 (PSEUDO 검수필요)","entities":["NAME","ORG","ADDRESS"],"note":"대화 weak"}
_CAP=30000
def collect(limit:int=0)->dict:
    cap=limit or _CAP; texts=[]
    for fp in glob.glob(str(_DIR/"**"/"*.jsonl"),recursive=True):
        if 'cache' in fp: continue
        for line in open(fp,encoding="utf-8"):
            line=line.strip()
            if not line: continue
            try: o=json.loads(line)
            except: continue
            t=" ".join(str(o.get(k,"")) for k in ("instruction","input","output") if o.get(k))
            if t.strip(): texts.append(t)
            if len(texts)>=cap: break
        if len(texts)>=cap: break
    return {"kind":"weak_examples","license":META["license"],"examples":weak_label_texts(texts,min_len=20)}
