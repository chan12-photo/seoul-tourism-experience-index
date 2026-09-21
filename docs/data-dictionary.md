# 데이터 사전

## 공통 키

| 컬럼 | 형식 | 설명 |
|---|---|---|
| `administrative_dong_code` | string | 행정동 코드, 앞자리 0 보존 |
| `district` | string | 자치구명 |
| `administrative_dong` | string | 행정동명 |
| `key` | string | `district_administrative_dong` 결합 키 |

원본 코드의 한글 컬럼명은 공개 파이프라인에서 영문 이름으로 통일합니다. 원천자료를 불러올 때만 공급기관의 원래 컬럼명을 사용하고, 정제 직후 표준 이름으로 변환합니다.

## C축

| 컬럼 | 단위 | 방향 | 설명 |
|---|---:|---|---|
| `C1_culture_space_count` | 개 | 높을수록 긍정 | 행정동 내 문화공간 수 |
| `C2_tourist_attraction_count` | 개 | 진단용 | 지오코딩된 관광지 수, 최종 PCA 제외 |
| `C3_traditional_count` | 개 | 높을수록 긍정 | 전통·역사 관광 콘텐츠 수 |
| `C3_art_count` | 개 | 높을수록 긍정 | 문화·예술 관광 콘텐츠 수 |
| `C3_nature_count` | 개 | 높을수록 긍정 | 자연·힐링 관광 콘텐츠 수 |
| `C3_modern_count` | 개 | 높을수록 긍정 | 현대·한류·라이프스타일 콘텐츠 수 |
| `C3_classified_count` | 개 | 진단용 | 네 범주에 분류된 관광지 합계 |
| `C3_shannon_entropy` | 지수 | 높을수록 다양 | 네 범주 비율의 Shannon entropy |
| `C4_classification_completion_ratio` | 0~1 | 높을수록 긍정 | 분류 건수 / 전체 관광지 수 |
| `C5_heritage_count` | 개 | 높을수록 긍정 | 장소형 문화유산 수 |
| `C5_heritage_log_count` | log(1+x) | 높을수록 긍정 | 문화유산 수의 로그 변환값 |

## D축

| 컬럼 | 단위 | 방향 | 설명 |
|---|---:|---|---|
| `D1_subway_count` | 개 | 높을수록 긍정 | 행정동 내 지하철역 수 |
| `D2_nearest_hub` | category | 해당 없음 | 가장 가까운 4대 관광거점 |
| `D2_min_distance_km` | km | 낮을수록 긍정 | 행정동 중심점과 최근접 거점의 직선거리 |
| `D2_distance_score` | 0~1 | 높을수록 긍정 | 거리의 reverse min-max 점수, 진단용 |
| `D2_access` | km 부호반전 | 높을수록 긍정 | PCA 입력용 `-D2_min_distance_km` |
| `D3_bus_stop_count` | 개 | 높을수록 긍정 | 행정동 내 고유 버스정류장 수 |

## PCA와 최종 지수

| 컬럼 | 설명 |
|---|---|
| `C_axis_PC1` | C축 표준화 변수의 제1주성분 |
| `D_axis_PC1` | D축 표준화 변수의 제1주성분 |
| `TEI_supply_score` | A·B·C·D 축 점수의 동일가중 평균 |
| `tourism_demand_score` | 관광소비와 단기체류 외국인 생활인구 결합점수 |
| `quadrant` | 공급·수요 중앙값 기준 사분면 |

