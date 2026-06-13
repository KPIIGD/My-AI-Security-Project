"""KLUE-NER external transfer abort callback (v2 trap guard).

v2 실패 패턴 — KLUE 외부 macro-F1 0.766 → 0.664 박살. 본 callback 은 매 epoch
끝나면 klue_test split 으로 평가해서 임계값 미만이면 즉시 학습을 중단한다.

NEXT_SESSION.md "v2 트랩 모니터링":
  외부 transfer 모니터: 매 epoch klue_test eval. 0.764 (v1) 또는 0.766 (v3) 아래로
  떨어지면 즉시 중단.

용법 (train_v4.py 에서):
  from klue_abort_callback import KlueAbortCallback
  cb = KlueAbortCallback(klue_test_ds, threshold=0.766)
  trainer2.add_callback(cb)

산출:
  - 각 epoch 의 klue_test macro_f1 을 stdout + JSON 로그로 남김
  - threshold 미달 시 control.should_training_stop = True 로 학습 종료
  - trainer 종료 후 last_eval_metrics / aborted 속성으로 결과 회수 가능
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from transformers import TrainerCallback, TrainerControl, TrainerState


class KlueAbortCallback(TrainerCallback):
    """매 epoch 종료 후 klue_test 평가 → threshold 미달 시 학습 중단."""

    def __init__(
        self,
        klue_test_dataset,
        threshold: float = 0.766,
        log_path: Optional[str] = None,
        metric_key: str = "eval_macro_f1",
    ):
        """
        Args:
            klue_test_dataset: PIINerDataset 인스턴스 (klue_test split)
            threshold: 이 값 미만이면 abort. v3 baseline 0.766 기준.
            log_path: 각 epoch eval 결과를 append 할 JSONL 경로 (선택).
            metric_key: trainer.evaluate() 결과 dict 에서 비교할 key.
                기본은 'eval_macro_f1' (train_v4.py 의 compute_metrics 출력 가정).
        """
        self.klue_test_dataset = klue_test_dataset
        self.threshold = float(threshold)
        self.log_path = Path(log_path) if log_path else None
        self.metric_key = metric_key
        self.history: list[dict] = []
        self.aborted: bool = False
        self.last_eval_metrics: dict = {}

    def on_evaluate(
        self,
        args,
        state: TrainerState,
        control: TrainerControl,
        **kwargs,
    ):
        """val_ds eval 직후 호출. 같은 시점에 klue_test 도 평가."""
        trainer = kwargs.get("model")  # NOTE: HF 는 trainer 자체를 넘기지 않음
        # Trainer 객체는 외부에서 주입받아야 evaluate() 호출 가능.
        # 대안: tokenizer / data_collator / model 받아서 직접 eval loop 돌리기.
        # 가장 단순한 방법은 콜백 등록 시 trainer 참조를 직접 attribute 로 박는 것.
        trainer = getattr(self, "_trainer", None)
        if trainer is None:
            print("[KlueAbortCallback] WARN: trainer 미연결, klue eval 스킵")
            return control

        print(f"\n[KlueAbortCallback] epoch={state.epoch:.2f} KLUE test eval...")
        metrics = trainer.evaluate(
            self.klue_test_dataset,
            metric_key_prefix="klue_test",
        )
        # metric key 가 prefix 다르게 나옴 (eval_macro_f1 → klue_test_macro_f1)
        for candidate in (
            f"klue_test_{self.metric_key.replace('eval_', '')}",
            self.metric_key,
            "klue_test_macro_f1",
            "eval_macro_f1",
        ):
            if candidate in metrics:
                klue_f1 = float(metrics[candidate])
                used_key = candidate
                break
        else:
            print(f"[KlueAbortCallback] ERROR: macro_f1 key 없음. keys={list(metrics)}")
            return control

        self.last_eval_metrics = dict(metrics)
        record = {
            "epoch": float(state.epoch),
            "global_step": int(state.global_step),
            "klue_macro_f1": klue_f1,
            "metric_key_used": used_key,
            "all_metrics": {k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))},
        }
        self.history.append(record)

        if self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"[KlueAbortCallback] KLUE macro-F1={klue_f1:.4f}  threshold={self.threshold:.4f}")

        if klue_f1 < self.threshold:
            self.aborted = True
            print(
                f"\n*** v2 TRAP 가드 작동 ***\n"
                f"KLUE 외부 macro-F1 {klue_f1:.4f} < 임계값 {self.threshold:.4f}\n"
                f"NER CLAUDE.md §6 + NEXT_SESSION.md 트랩 모니터링 → 즉시 학습 중단\n"
            )
            control.should_training_stop = True
        return control


def attach_to_trainer(callback: KlueAbortCallback, trainer) -> None:
    """trainer 참조를 callback 내부에 주입 (on_evaluate 에서 evaluate() 호출 가능하게)."""
    callback._trainer = trainer
    trainer.add_callback(callback)
