"""Collector (Phase B weak): daekeun-ml naver 뉴스요약 — document (뉴스 본문)."""
from __future__ import annotations
import glob,csv,sys
from pathlib import Path
from ._text_weak import weak_label_texts
csv.field_size_limit(min(sys.maxsize,2**31-1))
_DIR=Path(__file__).resolve().parents[2]/"data"/"external"/"huggingface"/"daekeun-ml__naver-news-summarization-ko"
META={"id":"naver_news_weak","kind":"weak_examples","license":"daekeun-ml/HF 뉴스요약 (PSEUDO 검수필요)","entities":["NAME","ORG","ADDRESS"],"note":"뉴스 본문 weak"}
def collect(limit:int=0)->dict:
    texts=[]
    for fp in glob.glob(str(_DIR/"*.csv")):
        for row in csv.DictReader(open(fp,encoding="utf-8")):
            t=row.get("document") or row.get("text") or row.get("contents") or ""
            if t: texts.append(t)
            if limit and len(texts)>=limit: break
    return {"kind":"weak_examples","license":META["license"],"examples":weak_label_texts(texts,min_len=40)}
