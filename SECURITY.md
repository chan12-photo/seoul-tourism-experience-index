# Security

API 키와 토큰은 환경변수로만 주입하고 저장소에 저장하지 않습니다. 공개 전 다음 명령으로 기본 검사를 실행합니다.

```bash
tei-pipeline check-public .
```

검사기는 다음 항목을 차단합니다.

- `.env` 변형, API 키·Bearer 토큰·GitHub 토큰·개인키 패턴
- Shapefile·스프레드시트·압축파일과 10 MiB 초과 파일
- `data/raw`, `data/interim`, `data/processed` 아래의 실제 데이터 파일
- 자격증명으로 의심되는 파일명

이 검사는 휴리스틱 방어선이며 모든 비밀정보를 보장해서 탐지하지는 않습니다. GitHub secret scanning과 push protection을 함께 사용하고, 공개 전 변경 파일을 사람이 다시 검토해야 합니다.

비밀정보가 커밋된 경우 커밋을 지우기 전에 해당 키를 즉시 폐기해야 합니다. Git 기록에서 문자열을 제거하더라도 이미 노출된 키는 다시 안전해지지 않습니다.
