# Portfolio assets

이 폴더의 이미지는 최종보고서와 로컬 분석 산출물에서 공개 가능한 집계 수치만 재구성한 포트폴리오용 시각 자료입니다. 원천 데이터, 행정동별 CSV, API 응답과 좌표는 포함하지 않습니다.

재생성 예시:

```bash
python -m pip install -e ".[viz]"
python scripts/build_portfolio_assets.py \
  --final-results /local/path/to/final-pca-result.csv \
  --archive-root /local/path/to/TEI_CD_axis \
  --output-dir assets
```

스크립트는 다음 값이 원본 최종 산출물과 일치할 때만 이미지를 생성합니다.

- 분석 행정동 426개
- Pearson 상관계수 약 0.676
- 사분면별 행정동 수 164·49·164·49개
- 문화공간 1,051건, 유효 관광지 1,009건, 분류 완료 696건
- 장소형 문화유산 271건, 지하철역 333개, 버스정류장 11,222개
- 주요 거점별 최근접 행정동 수와 거리의 최솟값·평균·최댓값
- 중앙동·우이동·상일2동의 4사분면 포함 여부와 보고서 기재 축 점수

이미지를 갱신할 때는 원천자료의 외부 공개 가능 여부와 팀 공동 저작물 사용 범위를 먼저 확인해야 합니다.
