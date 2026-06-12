"""
Phase 1 — A.3 False Positive Rate on Normal Korean Text

Tests Layer 0 detector against clean Korean documents (no PII) to measure
false positive rate. Uses curated normal text samples:
 - news excerpts (일반 사회/경제/스포츠)
 - business emails / announcements
 - casual conversation
 - technical documentation
"""
import json
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "c:/My-AI-Security-Project/PII/layer_0")

from korean_pii_detector import KoreanPIIDetector

NORMAL_DOCS = [
    # 뉴스 기사 스타일
    "오늘 증시는 코스피 2450.32 포인트로 마감했으며 전일 대비 1.2% 상승했다.",
    "한국은행이 기준금리를 동결하기로 결정했다고 발표했다.",
    "서울 시내 주요 지역에서 벚꽃이 만개하면서 시민들의 나들이 발걸음이 이어지고 있다.",
    "올해 하반기 경제 성장률 전망치가 당초 예상보다 0.3%p 상향 조정되었다.",
    "반도체 수출이 3개월 연속 증가세를 보이며 무역수지 개선에 기여했다.",
    "기상청은 이번 주 전국적으로 맑은 날씨가 이어질 것이라고 예보했다.",
    "신종 감염병 대응을 위한 정부 합동 대책회의가 개최되었다.",
    "스포츠계에서 올림픽 대표팀 최종 명단이 확정되었다는 소식이다.",
    "환경부는 탄소 중립 목표 달성을 위한 5개년 계획을 발표했다.",
    "교육부가 내년도 수능 시험 출제 방침을 공개했다.",

    # 이메일/공지
    "안녕하세요. 이번 주 회의는 금요일 오후 3시에 대회의실에서 진행됩니다.",
    "프로젝트 중간 보고서 제출 기한이 다음 주 금요일로 변경되었으니 참고 부탁드립니다.",
    "사내 교육 프로그램 신청을 받고 있습니다. 관심 있으신 분은 HR팀에 문의 주세요.",
    "분기별 실적 검토 미팅이 예정되어 있습니다. 각 팀장님은 자료를 준비해 주시기 바랍니다.",
    "사옥 이전에 따른 업무 공간 안내드립니다. 3층은 개발팀, 5층은 경영지원팀입니다.",
    "신규 협력사 등록 프로세스가 개선되었습니다. 자세한 내용은 매뉴얼을 참조하세요.",
    "연말정산 자료 제출 기한이 임박했습니다. 해당 서류를 준비해 주세요.",
    "해외 출장 시 유의사항과 비용 처리 방법에 대해 안내드립니다.",
    "보안 교육 이수 현황을 확인해 주시기 바랍니다. 미이수자는 재수강해야 합니다.",
    "복리후생 제도가 일부 개편되었습니다. 상세 내용은 사내 포털을 확인해 주세요.",

    # 일상 대화
    "오늘 점심에 뭐 먹을까요? 근처에 새로 생긴 식당이 맛있다는 것 같던데.",
    "어제 본 영화 정말 재미있었어요. 다음 번에는 같이 보러 가요.",
    "주말에 가족들이랑 여행을 다녀왔는데 날씨가 너무 좋았어요.",
    "새로 시작한 운동이 아직 어색하지만 꾸준히 해보려고 합니다.",
    "집에 오는 길에 꽃집에 들렀는데 꽃이 정말 예쁘더라고요.",
    "요즘 읽고 있는 책이 너무 흥미진진해서 밤새 읽을 뻔했어요.",
    "친구가 이사를 간다고 해서 집들이 선물을 사러 갔어요.",
    "취미로 시작한 베이킹이 이제는 나름 실력이 좀 늘었어요.",
    "등산을 좋아해서 주말마다 근교 산을 찾아다닙니다.",
    "새로 배우기 시작한 외국어가 어렵긴 하지만 재미있어요.",

    # 기술 문서 스타일
    "본 시스템은 클라이언트-서버 아키텍처로 구성되어 있으며 RESTful API를 제공합니다.",
    "데이터베이스는 관계형 DB를 사용하며 트랜잭션 격리 수준은 기본값을 따릅니다.",
    "비동기 처리를 위해 메시지 큐를 도입하여 시스템 확장성을 확보했습니다.",
    "인증 방식은 OAuth 2.0 표준을 따르며 JWT 토큰 기반 세션 관리를 지원합니다.",
    "로그 수집 및 분석을 위해 ELK 스택을 활용하고 있습니다.",
    "컨테이너 오케스트레이션은 Kubernetes를 통해 관리됩니다.",
    "CI/CD 파이프라인은 GitLab CI를 기반으로 구축되어 있습니다.",
    "성능 모니터링 도구로 Prometheus와 Grafana를 연동하여 사용하고 있습니다.",
    "백업 정책은 일일 전체 백업과 증분 백업을 병행합니다.",
    "재해 복구를 위한 이중화 구성이 필수 요구사항입니다.",

    # 학술/논문 스타일
    "본 연구에서는 기존 방법론의 한계를 극복하기 위한 새로운 접근 방식을 제시한다.",
    "실험 결과는 제안하는 방법이 기존 대비 유의미한 성능 향상을 보임을 시사한다.",
    "데이터 수집 과정에서 윤리적 고려사항을 반영하여 개인정보 보호에 주의를 기울였다.",
    "문헌 조사를 통해 해당 분야의 최신 동향을 파악하고 연구 방향을 설정하였다.",
    "통계적 검정을 통해 가설의 유의성을 확인한 결과 기각되지 않았다.",
    "본 연구의 한계점과 향후 연구 방향에 대해 논의하고자 한다.",
    "제안 모델은 기존 베이스라인 대비 정확도와 속도 모두에서 개선을 보였다.",
    "선행 연구들과 달리 본 연구는 다양한 도메인에 걸친 범용성을 고려했다.",
    "결론적으로 본 연구는 학술적 기여와 실무적 함의를 동시에 제공한다고 할 수 있다.",
    "추후 연구에서는 더 큰 규모의 데이터셋을 활용한 검증이 필요하다.",
]

detector = KoreanPIIDetector()

total = len(NORMAL_DOCS)
fp_docs = []
findings_by_type = {}

for doc in NORMAL_DOCS:
    findings = detector.detect(doc)
    if findings:
        fp_docs.append({"doc": doc, "findings": [
            {"type": f.pii_type, "value": f.value, "keyword": f.context_keyword}
            for f in findings
        ]})
        for f in findings:
            findings_by_type[f.pii_type] = findings_by_type.get(f.pii_type, 0) + 1

fp_rate = 100 * len(fp_docs) / total

print("=" * 78)
print("  A.3 — False Positive Rate on Normal Korean Text (n=50)")
print("=" * 78)
print(f"\nTotal clean documents tested: {total}")
print(f"Documents with any finding    : {len(fp_docs)}  ({fp_rate:.2f}%)")
print(f"Clean pass rate               : {100-fp_rate:.2f}%")

if findings_by_type:
    print(f"\nFalse positive breakdown:")
    for t, c in sorted(findings_by_type.items(), key=lambda x: -x[1]):
        print(f"  {t:20s}: {c}")
    print(f"\nFirst 5 FP cases (for inspection):")
    for f in fp_docs[:5]:
        print(f"\n  DOC: {f['doc'][:80]}")
        for finding in f["findings"][:3]:
            print(f"    → {finding['type']:15s} | {finding['value'][:40]} | {finding['keyword']}")

json.dump({
    "total": total,
    "fp_docs_count": len(fp_docs),
    "fp_rate_percent": round(fp_rate, 2),
    "findings_by_type": findings_by_type,
    "fp_samples": fp_docs,
}, open("phase1_fp_test.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nSaved: phase1_fp_test.json")
