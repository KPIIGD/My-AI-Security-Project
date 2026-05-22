"""Korean PII Guardrail v0.2 — 통합 데모 (교수 발표용)

3 tabs:
  ① 라이브 탐지/마스킹   — 텍스트 입력 → 실시간 PII 하이라이트 + 마스킹
  ② 성능 대시보드        — ablation 단계별 기여 + latency(ONNX 4x) + release gate
  ③ 공격 → 방어 스토리   — 한국어 변이가 프로덕션 가드레일을 뚫고, 우리 L0가 잡는다

실행:
    cd korean_pii_guardrail_v0_2
    python demo/app.py
    # 브라우저에서 http://127.0.0.1:7860
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import gradio as gr
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams

# --- 한글 폰트 (Windows) ---
for _fp in ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/NanumGothic.ttf"):
    if Path(_fp).exists():
        font_manager.fontManager.addfont(_fp)
        rcParams["font.family"] = font_manager.FontProperties(fname=_fp).get_name()
        break
rcParams["axes.unicode_minus"] = False

from pii_guardrail.pipeline import GuardrailPipeline, default_components
from pii_guardrail.schema import GuardrailRequest

DEMO_DIR = Path(__file__).resolve().parent
if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))
from pipeline_trace import render_trace_html, trace_pipeline  # noqa: E402

ASSETS = DEMO_DIR / "assets"
CONFIG_DIR = PROJECT_ROOT / "configs"

# NER 모델: 로컬 학습 산출물이 있으면 그것, 없으면 HuggingFace Hub에서 자동 다운로드.
# repo 어디에 clone하든 찾도록 repo-relative 후보를 먼저 본 뒤, 레거시 절대경로,
# 마지막으로 Hub 모델로 fallback. (다른 사람이 clone 후 바로 실행 가능)
_NER_CANDIDATES = [
    PROJECT_ROOT.parent / "PII" / "ner" / "models" / "pii_ner_v3" / "final",  # repo-relative
    Path(r"C:/My-AI-Security-Project/PII/ner/models/pii_ner_v3/final"),       # legacy 절대경로
]
NER_MODEL_PATH = next(
    (str(p) for p in _NER_CANDIDATES if p.is_dir()),
    "vmaca123/korean-pii-ner-v3",  # HuggingFace Hub
)

# 대시보드용 측정 데이터/그림은 demo/assets/ 에 동봉 (환경 독립)
REPORTS = ASSETS
NER_REPORTS = ASSETS
FIG_DIR = ASSETS / "figs"


# ============================================================
# Pipeline 초기화 (real NER, 기본 fail-closed)
# ============================================================
# 데모는 "real NER v3 라이브" 라는 메시지를 전제로 한다. real NER 로드에 실패하면
# 기본적으로 fail-closed (즉시 중단) 한다. mock NER 로의 fallback 은 mock 임을
# 명시적으로 허용했을 때(--allow-mock)만 가능하며, 이때는 대시보드의 성능 수치를
# "현재 라이브 측정치"로 오인하지 않도록 mock 경고를 노출한다.
MOCK_MODE = False


class NERLoadError(RuntimeError):
    """real NER v3 로드 실패 (fail-closed)."""


def build_pipeline(allow_mock: bool = False):
    global MOCK_MODE
    try:
        from pii_guardrail.ner.finetuned_wrapper import FinetunedNERDetector

        ner = FinetunedNERDetector(model_path=NER_MODEL_PATH)
        pipe = GuardrailPipeline(default_components(config_dir=CONFIG_DIR, ner_detector=ner))
        # warmup (모델 lazy-load 강제) — 여기서 실패하면 real NER 미작동으로 간주
        pipe.process(GuardrailRequest(text="홍길동 010-1234-5678"))
        return pipe, f"✅ Real NER v3 (klue-roberta-large, {NER_MODEL_PATH})"
    except Exception as exc:
        if not allow_mock:
            raise NERLoadError(
                f"real NER v3 로드 실패: {exc}\n"
                "데모는 기본적으로 real NER 를 요구합니다(fail-closed). "
                "mock NER 로 강제 실행하려면 --allow-mock 옵션을 쓰세요. "
                "단, 이 경우 대시보드 성능 수치는 현재 추론 결과가 아닙니다."
            ) from exc
        print(f"[demo] real NER 로드 실패 → mock NER 사용(--allow-mock): {exc}")
        MOCK_MODE = True
        pipe = GuardrailPipeline(default_components(config_dir=CONFIG_DIR))
        return pipe, f"⚠️ Mock NER (real NER 로드 실패: {exc})"


# 파이프라인은 __main__ 에서 옵션(--allow-mock)을 읽은 뒤 빌드한다 (fail-closed 제어).
PIPELINE = None
NER_MODE = "(미초기화)"

# --share(공개 링크) 모드에서는 탐지된 원문 PII 값을 public UI에 노출하지 않는다.
# (로컬 전용일 때만 원문 표시 — 프로젝트의 no-raw-PII 경계 준수)
SHARE_MODE = False


# 엔티티 타입별 색상 (HighlightedText)
ENTITY_COLORS = {
    "PERSON_NAME": "#ff6b6b",
    "ADDRESS_FULL": "#4ecdc4",
    "ORGANIZATION": "#ffd93d",
    "RRN": "#ff8c42",
    "FRN": "#ff8c42",
    "PHONE_MOBILE": "#6bcB77",
    "PHONE_LANDLINE": "#6bcB77",
    "EMAIL": "#a78bfa",
    "CREDIT_CARD": "#f06595",
    "BANK_ACCOUNT": "#f06595",
    "BUSINESS_REG_NO": "#ffa94d",
    "API_KEY_SECRET": "#e64980",
    "IP_ADDRESS": "#74c0fc",
}

# masked_text 의 placeholder family ([PERSON_1] 등) → HighlightedText 색상 라벨.
# share 모드에서 원문 대신 placeholder 만 하이라이트할 때 색을 맞추기 위함.
_MASK_FAMILY_TO_LABEL = {
    "PERSON": "PERSON_NAME",
    "PHONE": "PHONE_MOBILE",
    "ADDRESS": "ADDRESS_FULL",
    "ID": "RRN",
    "SECRET": "API_KEY_SECRET",
}
_PLACEHOLDER_RE = re.compile(r"\[([A-Z][A-Z0-9]*)_(\d+)\]")


def _masked_segments(masked: str) -> list[tuple[str, str | None]]:
    """share 모드용: masked_text 의 placeholder 토큰만 하이라이트한다.

    masked_text 는 탐지된 PII 가 [FAMILY_N] placeholder 로 치환된, downstream 에
    전달되는 안전한 출력이다. 따라서 여기엔 원문 PII 값이 들어있지 않으므로
    public(share) UI 에 노출해도 no-raw-PII 경계를 위반하지 않는다.
    """
    segments: list[tuple[str, str | None]] = []
    cursor = 0
    for m in _PLACEHOLDER_RE.finditer(masked):
        if m.start() > cursor:
            segments.append((masked[cursor:m.start()], None))
        family = m.group(1)
        segments.append((m.group(0), _MASK_FAMILY_TO_LABEL.get(family, family)))
        cursor = m.end()
    if cursor < len(masked):
        segments.append((masked[cursor:], None))
    return segments or [(masked, None)]


# ============================================================
# Tab ① 라이브 탐지/마스킹
# ============================================================
def analyze(text: str):
    text = (text or "").strip()
    if not text:
        return [("입력 텍스트가 없습니다.", None)], "", [], "—"

    t0 = time.perf_counter()
    response = PIPELINE.process(GuardrailRequest(text=text))
    latency_ms = (time.perf_counter() - t0) * 1000.0

    spans = sorted(response.spans, key=lambda s: s.start)

    masked = response.masked_text
    if response.blocked:
        masked = "🚫 BLOCKED — 고위험 PII 다수 탐지로 요청 차단됨"
    elif masked is None:
        masked = text

    # HighlightedText 분할.
    #   - 로컬 모드: 원문을 span 경계로 분할해 실제 PII 를 하이라이트 (시연용).
    #   - share 모드: 원문 대신 masked_text(placeholder)만 하이라이트 → public 에
    #     raw PII 노출 방지 (no-raw-PII 경계). 원문값/raw offset slice 를 쓰지 않는다.
    segments: list[tuple[str, str | None]]
    if SHARE_MODE:
        if response.blocked:
            segments = [("🚫 BLOCKED — 고위험 PII 다수 탐지로 요청 차단됨", None)]
        else:
            segments = _masked_segments(masked)
    else:
        segments = []
        cursor = 0
        for span in spans:
            if span.start > cursor:
                segments.append((text[cursor:span.start], None))
            segments.append((text[span.start:span.end], span.entity_type.value))
            cursor = span.end
        if cursor < len(text):
            segments.append((text[cursor:], None))
        if not segments:
            segments = [(text, None)]

    def _span_value(span) -> str:
        # share 모드: 원문값 대신 길이만 (public 노출 방지). 로컬: 원문 표시.
        if SHARE_MODE:
            return f"🔒 {span.end - span.start}자 (로컬 전용)"
        return text[span.start:span.end]

    table = [
        [
            span.entity_type.value,
            _span_value(span),
            span.risk_level.value,
            span.action.value,
            round(span.score, 2),
        ]
        for span in spans
    ]

    stats = (
        f"⏱ {latency_ms:.0f} ms  |  🔍 {len(spans)}개 PII 탐지  |  "
        f"{'🚫 차단' if response.blocked else '🟡 마스킹' if spans else '✅ PII 없음'}"
    )
    return segments, masked, table, stats


LIVE_EXAMPLES = [
    "최영희 연락처 010-1234-5678, 이메일 choi@example.com",
    "김민수 주민번호 900101-1234568, 서울시 강남구 테헤란로 123 거주",
    "하도윤 신한은행 계좌 110-123-456789, 카드 4532015112830036",
    "담당자 박지성 (지성테크 대표) ceo@jisung.co.kr 010-9876-5432",
    "내 ㅈㅜㅁㅣㄴ번호는 9​0​0​1​0​1-1234568 이야",  # 변이(자모분해+zero-width)
]


# ============================================================
# Tab ② 성능 대시보드
# ============================================================
def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# 엔티티 타입 → 한글 라벨 (대시보드 가독성)
ENTITY_KO = {
    "PERSON_NAME": "이름",
    "ADDRESS_FULL": "주소",
    "ADDRESS_UNIT": "주소(부분)",
    "ORGANIZATION": "조직",
    "PHONE_MOBILE": "휴대폰",
    "PHONE_LANDLINE": "유선전화",
    "EMAIL": "이메일",
    "RRN": "주민번호",
    "FRN": "외국인번호",
    "CREDIT_CARD": "신용카드",
    "BANK_ACCOUNT": "계좌번호",
    "BUSINESS_REG_NO": "사업자번호",
    "API_KEY_SECRET": "API 키",
    "IP_ADDRESS": "IP주소",
    "MAC_ADDRESS": "MAC주소",
    "HOSPITAL": "병원",
    "CUSTOMER_ID": "고객ID",
    "MEDICAL_RECORD_NO": "의무기록번호",
    "STUDENT_ID": "학번",
    "EMPLOYEE_ID": "사번",
}


def kpi_cards() -> str:
    """큰 숫자 KPI 카드 4개 (HTML)."""
    qa = _load_json(NER_REPORTS / "quantization_accuracy.json")
    lat = _load_json(NER_REPORTS / "latency_bench.json")
    agree = (qa.get("overall_agreement", 0) * 100) if qa else 99.75
    speedup = (lat.get("speedup_int8_p50") if lat else None) or 4.04
    cards = [
        ("87.8%", "한국어 NER macro-F1", "klue-roberta-large 직접 fine-tune (internal test)", "#4263eb"),
        ("막아냄", "한국어 변이 공격 방어", "자모분해 · zero-width · 띄어쓰기", "#37b24d"),
        (f"{speedup:.1f}×", "추론 속도 가속 (별도 벤치마크)", "ONNX INT8 · 135ms · CPU — 라이브 경로 아님", "#f59f00"),
        ("0건", "가짜 PII 오탐", "체크섬 검증 · 원문 로깅 0", "#e64980"),
    ]
    html = ""
    if MOCK_MODE:
        html += (
            '<div style="background:#fff3bf;border:1px solid #f59f00;border-radius:10px;'
            'padding:12px 14px;margin:8px 0;font-weight:700;color:#664d03">'
            "⚠️ 현재 <b>Mock NER</b> 로 실행 중입니다. 아래 성능 수치는 real NER v3 의 "
            "별도 측정/벤치마크 결과이며, <b>지금 화면의 탐지 결과와 무관</b>합니다."
            "</div>"
        )
    html += '<div style="display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 4px">'
    for big, title, sub, color in cards:
        html += (
            f'<div style="flex:1;min-width:175px;background:{color}1a;'
            f'border:1px solid {color}66;border-radius:14px;padding:18px 14px;text-align:center">'
            f'<div style="font-size:34px;font-weight:800;color:{color};line-height:1.1">{big}</div>'
            f'<div style="font-size:15px;font-weight:700;margin-top:6px">{title}</div>'
            f'<div style="font-size:12px;opacity:0.72;margin-top:3px">{sub}</div></div>'
        )
    html += "</div>"
    return html


def plot_entity_detection():
    """한국어 PII 종류별 탐지율 (real NER 평가 결과)."""
    data = _load_json(REPORTS / "eval_real_ner.json")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    if not data or "per_entity" not in data:
        ax.text(0.5, 0.5, "평가 데이터 생성 중…", ha="center", va="center")
        ax.axis("off")
        return fig
    rows = [
        (ENTITY_KO.get(m["entity_type"], m["entity_type"]), m["recall"] * 100)
        for m in data["per_entity"]
        if (m["tp_exact"] + m["tp_partial"] + m["fn"]) > 0
    ]
    rows.sort(key=lambda x: x[1])
    labels = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    colors = ["#37b24d" if v >= 80 else "#f59f00" if v >= 50 else "#fa5252" for v in vals]
    bars = ax.barh(labels, vals, color=colors)
    for bar, v in zip(bars, vals):
        ax.text(min(v + 2, 104), bar.get_y() + bar.get_height() / 2, f"{v:.0f}%", va="center", fontsize=9)
    ax.set_xlim(0, 112)
    ax.set_xlabel("탐지율 (recall, %)")
    ax.set_title("한국어 PII 종류별 탐지율")
    fig.tight_layout()
    return fig


def plot_latency():
    data = _load_json(NER_REPORTS / "latency_bench.json")
    fig, ax = plt.subplots(figsize=(7, 4))
    if not data:
        ax.text(0.5, 0.5, "latency 데이터 없음", ha="center")
        return fig
    labels, p50s, colors = [], [], []
    for key, color in (("pytorch", "#adb5bd"), ("onnx_fp32", "#748ffc"), ("onnx_int8", "#37b24d")):
        node = data.get(key) or (data.get("onnx") if key == "onnx_fp32" else None)
        if node and node.get("p50_ms"):
            labels.append({"pytorch": "PyTorch FP32", "onnx_fp32": "ONNX FP32", "onnx_int8": "ONNX INT8"}[key])
            p50s.append(node["p50_ms"])
            colors.append(color)
    bars = ax.bar(labels, p50s, color=colors)
    for bar, val in zip(bars, p50s):
        ax.text(bar.get_x() + bar.get_width() / 2, val, f"{val:.0f}ms", ha="center", va="bottom", fontsize=10)
    ax.set_title("NER v3 추론 latency (CPU, 256자) — INT8 별도 벤치마크 (라이브 경로 아님)")
    ax.set_ylabel("p50 latency (ms)")
    fig.tight_layout()
    return fig


def gate_summary():
    qa = _load_json(NER_REPORTS / "quantization_accuracy.json")
    agree = qa.get("overall_agreement", 0) * 100 if qa else 0
    rows = [
        ["NER v3 macro-F1 (internal test)", "0.878", "—"],
        ["NER v3 macro-F1 (KLUE 외부)", "0.766", "—"],
        ["INT8 quantization 일치도", f"{agree:.2f}%" if agree else "99.75%", "FP32 대비"],
        ["INT8 latency p50", "135.5 ms", "PyTorch 547ms → 4.04x"],
        ["모델 크기", "322 MB", "FP32 1.3GB → 4x ↓"],
        ["raw PII 로깅 (release gate)", "0", "docs/08 §8"],
    ]
    return rows


# ============================================================
# Tab ③ 공격 → 방어
# ============================================================
ATTACK_EXAMPLES = [
    ("원본 (정상)", "주민번호 900101-1234568"),
    ("자모 분해", "ㅈㅜㅁㅣㄴ번호 900101-1234568"),
    ("Zero-width space 삽입", "주민번호 9​0​0​1​0​1-1234568"),
    ("이름+주소 복합", "김민수 서울시 강남구 테헤란로 123 거주"),
    ("이름+연락처", "최영희 010-1234-5678 choi@example.com"),
]


def _restored_form(variant_text: str, pre) -> str:
    """변이를 원래대로 복원한 텍스트를 고른다.

    zwsp/NFKC 류는 normalized_text가 직접 복원하고, 자모분해 류는
    별도 표기 변이형(jamo_composed 등)에서 한글로 복원된다.
    """
    if pre.normalized_text != variant_text:
        return pre.normalized_text
    for v in pre.variants:
        if getattr(v, "name", "") == "jamo_composed" and v.text != variant_text:
            return v.text
    for v in pre.variants:
        if v.text != variant_text:
            return v.text
    return pre.normalized_text


def attack_before_after(variant_text: str):
    """변이 입력 → L0 정규화로 복원 → 탐지/마스킹 흐름을 단계별로 반환."""
    from pii_guardrail.preprocess import preprocess_text

    pre = preprocess_text(variant_text)
    normalized = _restored_form(variant_text, pre)
    restored = "✨ 복원됨 (변이 제거)" if normalized != variant_text else "변화 없음"

    response = PIPELINE.process(GuardrailRequest(text=variant_text))
    detected = ", ".join(
        sorted({ENTITY_KO.get(s.entity_type.value, s.entity_type.value) for s in response.spans})
    ) or "없음"
    masked = response.masked_text or variant_text
    if response.blocked:
        masked = "🚫 BLOCKED"
    verdict = "✅ 탐지 + 마스킹 성공" if response.spans else "❌ 미탐지"

    # share 모드: ①입력 ②정규화 결과는 원문(변이 전/후 모두 PII 포함)이므로 public 에
    # 노출하지 않는다. 길이 + 복원 여부만 표시하고, 안전한 detected/masked/verdict 만 공개.
    if SHARE_MODE:
        input_view = f"🔒 변이 입력 {len(variant_text)}자 (로컬 전용)"
        norm_view = f"🔒 정규화 결과 {len(normalized)}자 — [{restored}]"
    else:
        input_view = variant_text
        norm_view = f"{normalized}\n\n[{restored}]"
    return input_view, norm_view, detected, masked, verdict


# ============================================================
# Tab ④ 파이프라인 해부 (M1→M8 단계별 trace)
# ============================================================
TRACE_EXAMPLES = [
    "최영희 연봉 7409만원 010-1234-5678 choi@example.com",
    "김민수 서울시 강남구 테헤란로 123 삼성전자 근무, 당뇨 진단",
    "내 ㅈㅜㅁㅣㄴ번호는 900101-1234568 이야",
    "박지성님께 010-9876-5432 로 연락주세요 (지성테크 대표)",
]


def trace_view(text: str):
    text = (text or "").strip()
    if not text:
        return "<div style='opacity:.6'>입력 텍스트가 없습니다.</div>"
    # share 모드면 원문 숨김(reveal_raw=False) — placeholder/길이만 노출
    trace = trace_pipeline(PIPELINE, GuardrailRequest(text=text), reveal_raw=not SHARE_MODE)
    return render_trace_html(trace)


# ============================================================
# UI
# ============================================================
def build_ui():
    with gr.Blocks(title="Korean PII Guardrail v0.2 데모") as demo:
        gr.Markdown(
            f"""
            # 🛡️ 한국어 PII 가드레일 v0.2 — 라이브 데모
            **단일 통합 가드레일** = L0 정규화 + 정규식 + 사전 + NER(v3) + 문맥 + 정책/마스킹
            현재 NER 모드: **{NER_MODE}**
            <br><sub>라이브 추론 경로는 PyTorch(klue-roberta-large)입니다. 대시보드의 ONNX INT8·135ms·4.04× 는 별도 최적화 벤치마크 수치입니다.</sub>
            """
        )

        with gr.Tab("① 라이브 탐지/마스킹"):
            gr.Markdown("한국어 문장을 입력하면 PII를 실시간 탐지·마스킹합니다. 아래 예제를 눌러보세요.")
            with gr.Row():
                inp = gr.Textbox(label="입력 텍스트", lines=3, placeholder="예: 최영희 연봉 7409만원 010-1234-5678")
            with gr.Row():
                btn = gr.Button("🔍 분석", variant="primary")
            gr.Examples(examples=LIVE_EXAMPLES, inputs=inp)
            stats = gr.Markdown()
            hl = gr.HighlightedText(label="탐지된 PII (색상 = 엔티티 종류)", color_map=ENTITY_COLORS)
            masked_out = gr.Textbox(label="마스킹 결과 (downstream LLM에 전달되는 안전한 텍스트)", lines=3)
            table = gr.Dataframe(
                headers=["엔티티", "원문값", "위험도", "조치", "신뢰도"],
                label="탐지 상세",
                wrap=True,
            )
            btn.click(analyze, inputs=inp, outputs=[hl, masked_out, table, stats])
            inp.submit(analyze, inputs=inp, outputs=[hl, masked_out, table, stats])

        with gr.Tab("② 성능 대시보드"):
            gr.Markdown("## 📊 우리가 만든 것의 성능")
            gr.HTML(kpi_cards())
            with gr.Row():
                gr.Plot(plot_entity_detection())
                gr.Plot(plot_latency())
            with gr.Accordion("📋 상세 지표 더보기", open=False):
                gr.Dataframe(
                    value=gate_summary(),
                    headers=["지표", "값", "비고"],
                    wrap=True,
                )

        with gr.Tab("③ 공격 → 방어"):
            gr.Markdown(
                """
                ### 한국어 변이 공격 → 우리 가드레일이 잡는다
                프로덕션 가드레일(Presidio 등)은 자모 분해·zero-width·구분자 같은 한국어 변이에 뚫립니다.
                아래 변이를 우리 파이프라인에 흘려보면 **그래도 탐지/마스킹**됩니다 (L0 정규화 효과).
                """
            )
            atk = gr.Radio(
                choices=[t for _, t in ATTACK_EXAMPLES],
                label="변이 케이스 선택 (실제로 사람도 알아보기 힘든 형태)",
                value=ATTACK_EXAMPLES[1][1],
            )
            atk_btn = gr.Button("🛡️ 우리 가드레일로 처리", variant="primary")
            with gr.Row():
                atk_input = gr.Textbox(label="① 입력 (변이 공격 — 기존 가드레일은 여기서 놓침)", lines=3)
                atk_norm = gr.Textbox(label="② L0 정규화 결과 (변이를 원래대로 복원)", lines=3)
            with gr.Row():
                atk_detected = gr.Textbox(label="③ 탐지된 PII")
                atk_masked = gr.Textbox(label="④ 마스킹 결과")
                atk_verdict = gr.Textbox(label="⑤ 판정")
            atk_btn.click(
                attack_before_after,
                inputs=atk,
                outputs=[atk_input, atk_norm, atk_detected, atk_masked, atk_verdict],
            )
            gr.Markdown(
                "### 1차 캡스톤 측정 (8,400건 퍼저) — 우회율 / 성능 비교\n"
                "<sub>⚠️ 이 그래프는 1차 캡스톤(legacy) 결과로, `session`·`gps`·`court`·`crime` 등 "
                "v0.2 entity taxonomy 범위 밖 항목을 포함합니다. 현재 v0.2 시스템이 해당 범위를 "
                "지원한다는 의미가 아니며, 참고/비교용입니다.</sub>"
            )
            fig_files = [
                FIG_DIR / "fig1_overall_bypass.png",
                FIG_DIR / "fig5_l0_solo_pii.png",
                FIG_DIR / "fig13_ablation.png",
            ]
            existing = [str(f) for f in fig_files if f.exists()]
            if existing:
                gr.Gallery(
                    value=existing,
                    label="1차 캡스톤(legacy) 결과 그래프 — v0.2 범위 밖 항목 포함",
                    columns=3,
                    height=320,
                )

        with gr.Tab("④ 파이프라인 해부"):
            gr.Markdown(
                """
                ### M1 → M8 단계별 해부 (observability)
                입력 한 건이 **각 모듈(정규화 · 탐지 · 경계보정 · 문맥점수 · 해소 · 정책 · 마스킹 · 감사)**
                을 거치며 무엇을·어떻게·무슨 결과로 처리되는지 단계별로 보여줍니다.
                어느 단계에서 PII가 잡히고/놓치는지 눈으로 추적할 수 있습니다.
                """
            )
            tr_inp = gr.Textbox(label="입력 텍스트", lines=2,
                                placeholder="예: 최영희 연봉 7409만원 010-1234-5678")
            tr_btn = gr.Button("🔬 단계별 해부", variant="primary")
            gr.Examples(examples=TRACE_EXAMPLES, inputs=tr_inp)
            tr_out = gr.HTML()
            tr_btn.click(trace_view, inputs=tr_inp, outputs=tr_out)
            tr_inp.submit(trace_view, inputs=tr_inp, outputs=tr_out)

    return demo


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Korean PII Guardrail v0.2 데모")
    parser.add_argument(
        "--share",
        action="store_true",
        help="gradio.live 공개 링크 생성 (양유상 등 외부 리뷰용, 72시간 한시적)",
    )
    parser.add_argument(
        "--allow-mock",
        action="store_true",
        help="real NER v3 로드 실패 시 mock NER 로 fallback 허용 (기본은 fail-closed). "
             "이 경우 대시보드에 mock 경고가 표시됩니다.",
    )
    args = parser.parse_args()
    if args.share:
        SHARE_MODE = True
        print("[demo] SHARE 모드 — 원문 PII(하이라이트·표·공격 탭)를 숨깁니다 (public 노출 방지)")

    # 옵션 확정 후 파이프라인 빌드 (fail-closed: real NER 실패 시 --allow-mock 없으면 중단)
    try:
        PIPELINE, NER_MODE = build_pipeline(allow_mock=args.allow_mock)
    except NERLoadError as exc:
        print(f"[demo] {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[demo] NER mode: {NER_MODE}")
    ui = build_ui()
    # server_port 미지정 → gradio가 7860부터 빈 포트 자동 탐색 (좀비 점유 시 충돌 방지)
    ui.launch(server_name="127.0.0.1", inbrowser=False, share=args.share)
