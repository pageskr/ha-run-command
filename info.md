# Run Command Integration

[![hacs][hacsbadge]][hacs]

_웹 UI에서 설정 가능한 command_line 센서를 생성하는 Home Assistant 통합_

## 설치

### HACS (권장)

1. HACS에서 이 저장소를 사용자 정의 저장소로 추가
2. "Run Command" 통합 검색 후 설치
3. Home Assistant 재시작

### 수동 설치

1. 이 저장소의 모든 파일을 `custom_components/run_command/` 디렉토리에 복사
2. Home Assistant 재시작

## 설정

설정 → 통합 → 통합 추가 → Run Command

## 기능

- 웹 UI를 통한 간편한 센서 생성
- Jinja2 템플릿을 사용한 동적 명령어 실행
- 실행 주기 설정 가능
- 텍스트/JSON 결과 형식 지원
- 값 템플릿을 통한 결과 가공
- 속성 템플릿을 통한 커스텀 속성 생성

[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
