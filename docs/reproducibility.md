# 재현 방법

## 환경

- Python 3.11 이상
- 기본 분석: NumPy, pandas
- 공간처리: GeoPandas, Shapely, Pyogrio
- 포트폴리오 시각화: Matplotlib
- 테스트: pytest

`pyproject.toml`이 직접 의존성을 정의합니다. 완전히 동일한 실행환경이 필요한 공개 시점에는 잠금파일을 추가하고 데이터 버전과 해시를 함께 고정해야 합니다.

```bash
python -m venv .venv
source .venv/bin/activate
make install
make verify
```

`make verify`는 테스트, 린트, 포맷 검사, 모듈 컴파일, 의존성 무결성, 공개 안전 검사를 CI와 같은 범위로 실행합니다.

## 권장 파이프라인

1. 행정동 경계를 426개 기준행으로 정리합니다.
2. 모든 코드 열을 문자열로 읽어 앞자리 0을 보존합니다.
3. 점 자료의 좌표계와 서울시 범위를 검사합니다.
4. 고유 시설 식별자로 중복을 제거합니다.
5. 행정동 경계와 점 자료를 공간결합합니다.
6. C/D 원시 변수를 만들고 426행·키 유일성을 검사합니다.
7. PCA 입력에 결측치, 무한값, 상수 열이 없는지 검사합니다.
8. PCA 적합, 부호 정렬, 축 점수 표준화를 수행합니다.
9. A/B/C/D 축과 Y축을 결합하고 사분면을 계산합니다.
10. 결과 검증 후 공개 검사기를 실행합니다.

## 명령 예시

```bash
tei-pipeline validate-admin \
  --input data/processed/c_axis_features.csv \
  --keys administrative_dong_code \
  --expected-rows 426

tei-pipeline pca-axis \
  --input data/processed/d_axis_features.csv \
  --features D1_subway_count D2_access D3_bus_stop_count \
  --output-column D_axis_PC1 \
  --output data/processed/d_axis_pca.csv

tei-pipeline check-public .
```

## 검증 계약

- 최종 행정동 테이블은 정확히 426행이어야 합니다.
- 행정동 코드와 결합 키는 유일하고 결측이 없어야 합니다.
- 개수형 변수는 0 이상이어야 합니다.
- 비율형 변수는 0~1 범위여야 합니다.
- PCA 입력에는 결측, 무한값, 상수 열이 없어야 합니다.
- 시설 수 합계는 공간결합 성공 건수와 일치해야 합니다.
- 원본 행 수, 중복 제거 수, 좌표 실패 수, 공간결합 실패 수를 단계별로 기록해야 합니다.

## 현재 재현 범위

공개 버전은 원자료 재배포 제한 때문에 전체 결과 CSV를 포함하지 않습니다. 따라서 현재 CI는 실제 연구 수치가 아니라 합성데이터로 변환 함수, PCA, 검증과 보안검사를 테스트합니다. 실제 수치 재현을 주장하려면 승인된 입력자료, 해시, 실행 로그를 별도로 확보해야 합니다.
