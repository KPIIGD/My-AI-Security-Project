"""Collector (Phase B weak): heegyu korquad-chat — QA 대화 (text)."""
from __future__ import annotations
import glob,json
from pathlib import Path
from ._text_weak import weak_label_texts
_DIR=Path(__file__).resolve().parents[2]/"data"/"external"/"huggingface"/"heegyu__korquad-chat-v1"
META={"id":"korquad_chat_weak","kind":"weak_examples","license":"heegyu/HF korquad-chat (PSEUDO 검수필요)","entities":["NAME","ORG","ADDRESS"],"note":"QA 대화 weak"}
def collect(limit:int=0)->dict:
    texts=[]
    for fp in glob.glob(str(_DIR/"*.json")):
        try: data=json.load(open(fp,encoding="utf-8"))
        except: continue
        rows=data if isinstance(data,list) else data.get("data",[])
        for r in rows:
            t=r.get("text") if isinstance(r,dict) else None
            if t: texts.append(str(t))
            if limit and len(texts)>=limit: break
    return {"kind":"weak_examples","license":META["license"],"examples":weak_label_texts(texts,min_len=30)}
