"""
실 한국 행정구역 기반 주소 합성기.

Faker ko_KR.address()는 시·도와 시·군·구를 무작위 조합하므로 ("충청남도 삼척시" 등)
실 데이터가 아님. 또한 끝에 인명 포함 동·읍·면명을 괄호로 붙여 ADDR span을 오염시킴.

이 모듈은:
  1. korea-administrative-district 정적 데이터 (cosmosfarm/v20241209) 사용
  2. (광역시·도, 시·군·구) 실 페어만 추출
  3. 도로명 + 번지수 합성 (괄호 부속 텍스트 없음)
  4. 같은 시·군·구가 광역시·도마다 별개로 등장 가능 (e.g. 서울 중구 vs 부산 중구)

학습 데이터 NER ADDR span 안전성을 위함.
"""
from __future__ import annotations
import json
import random
from pathlib import Path
from typing import Optional

# 도로명 후보 (실제 한국 주요 도로명 일부)
ROAD_NAMES = [
    "강남대", "테헤란", "종로", "세종대", "을지", "충무", "퇴계", "남대문",
    "삼일대", "마포대", "한강대", "올림픽대", "동작대", "반포대", "노들",
    "강변북", "강변", "양재대", "선릉", "도산대", "압구정", "잠실", "송파대",
    "역삼", "삼성", "청계", "광화문", "명동", "남산", "한남대", "이태원",
    "보문", "청량리", "왕산", "수유", "도봉", "노원", "월계", "상계",
    "신촌", "연세", "이화여대", "홍익", "공덕", "여의대", "여의",
    "구로", "신도림", "오류", "개봉", "수궁", "독산", "시흥대",
    "사당", "방배", "서초중앙", "서초대", "강남", "분당수서",
    "수영", "광안", "해운대", "센텀", "해변", "동백", "온천",
    "달구벌대", "동대구", "중앙대", "신천대",
    "백제고분", "도청대", "녹지", "원평", "전대",
    "도원대", "원효대", "충장", "금남",
]

ROAD_TYPES = ["로", "길", "대로", "거리"]


def load_admin_pairs(json_path: Optional[Path] = None) -> list[tuple[str, str]]:
    """korea-administrative-district JSON → [(광역시·도, 시·군·구), ...] 리스트."""
    if json_path is None:
        json_path = Path(__file__).parent.parent / "data" / "korea_admin.json"
    with open(json_path, "r", encoding="utf-8") as f:
        d = json.load(f)
    pairs = []
    for entry in d["data"]:
        for sido, sigungu_list in entry.items():
            for sigungu in sigungu_list:
                pairs.append((sido, sigungu))
    return pairs


def build_address(rng: random.Random, sido: str, sigungu: str) -> str:
    """광역시·도 + 시·군·구 + 도로명 + 번호 형태로 주소 합성.

    예: "서울특별시 강남구 테헤란로 152"
    예: "부산광역시 해운대구 센텀로 23-4"
    """
    road_name = rng.choice(ROAD_NAMES)
    road_type = rng.choice(ROAD_TYPES)

    # 도로명에 숫자 prefix 일부 (e.g. "테헤란24길")
    if rng.random() < 0.3:
        road_name = f"{road_name}{rng.randint(1, 99)}"

    bunji = str(rng.randint(1, 999))
    if rng.random() < 0.4:
        bunji += f"-{rng.randint(1, 99)}"

    return f"{sido} {sigungu} {road_name}{road_type} {bunji}"


def random_address(rng: random.Random, pairs: list[tuple[str, str]]) -> str:
    """랜덤 (시·도, 시·군·구) 페어 + 도로명·번호."""
    sido, sigungu = rng.choice(pairs)
    return build_address(rng, sido, sigungu)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    pairs = load_admin_pairs()
    print(f"loaded {len(pairs)} (sido, sigungu) pairs")
    print(f"unique sido: {len(set(s for s, _ in pairs))}")
    print()
    rng = random.Random(42)
    for _ in range(15):
        print(random_address(rng, pairs))
