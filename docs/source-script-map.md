# 원본 스크립트 대응표

원본 작업폴더의 26개 스크립트는 탐색과 시행착오가 포함된 일회성 실행 파일입니다. 공개 버전은 기능 단위 모듈과 CLI로 재구성했습니다.

| 원본 단계 | 원본 목적 | 공개 버전 |
|---:|---|---|
| 01 | 서울 행정동 경계 구축 | 입력자료 제한으로 미포함, `spatial.py` 검증 규칙 적용 |
| 02 | 지하철역 행정동 집계 | `spatial.count_points_by_polygon` |
| 03 | 버스정류장 행정동 집계 | `spatial.count_points_by_polygon` |
| 04 | 지하철·버스 변수 결합 | `transport.build_transport_features` |
| 05 | 행정동 중심점 계산 | 공개 경계 승인 후 공간 전처리 단계에서 실행 |
| 06 | 행정동-관광거점 OD 조합 | `transport.nearest_hub_distance` 내부 cross join |
| 07 | 최근접 거점 직선거리 | `transport.haversine_km`, `nearest-hub` CLI |
| 08 | 초기 D축 가중합 | 최종 PCA와 달라 재현 코드에서 제외 |
| 09 | D축 결과 검사 | `validation.py`, 합성데이터 테스트 |
| 10 | 문화공간 행정동 집계 | `spatial.count_points_by_polygon` |
| 11 | 관광지 지오코딩·집계 | API 약관·키 보호 때문에 공개 코드에서 분리 |
| 12~13 | 초기 C1/C2 가중합·검사 | 최종 PCA와 달라 재현 코드에서 제외 |
| 14 | 관광 콘텐츠 분류·다양성 | `culture.add_content_metrics`, `scoring.shannon_entropy` |
| 15~16 | C3 포함 초기 C축·검사 | `culture.py`, `validation.py` |
| 17~20 | 문화유산 원천 탐색·입력 준비 | 방법론만 문서화, 원자료 미포함 |
| 21 | 문화유산 API 지오코딩 | API 약관·키 보호 때문에 공개 코드에서 분리 |
| 22~23 | 지오코딩 검증·행정동 집계 | `spatial.py`, 검토 규칙은 방법론에 기록 |
| 24 | 문화유산 로그 점수 | `culture.add_heritage_metrics` |
| 25 | C4 포함 초기 C축 가중합 | 최종 PCA와 달라 재현 코드에서 제외 |
| 26 | 초기 C/D 결합점수 | `pca.combine_axis_scores`의 일반화된 결합 로직 |

원본 `07_call_TMAP...`은 TMAP을 호출하지 않고 Haversine 거리를 계산했습니다. 공개 버전은 기능과 파일명이 일치하도록 수정했습니다. 또한 초기 `D3=거리`, `D4=버스`를 최종보고서의 `D2=거리`, `D3=버스`로 통일했습니다.

