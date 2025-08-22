# Run Command Integration for Home Assistant

웹 UI에서 설정 가능한 command_line 센서를 생성하는 Home Assistant 통합입니다.

**제작자**: Pages in Korea (pages.kr)

## 기능

- 웹 UI를 통한 간편한 센서 생성
- Jinja2 템플릿을 사용한 동적 명령어 실행
- 실행 주기 설정 가능
- 텍스트/JSON 결과 형식 지원
- 값 템플릿을 통한 결과 가공
- 속성 템플릿을 통한 커스텀 속성 생성
- 센서 설정 수정 기능

## 설치

### HACS를 통한 설치 (권장)

1. HACS에서 사용자 정의 저장소로 추가: `https://github.com/pages-kr/ha-run-command`
2. "Run Command" 통합 검색 후 설치
3. Home Assistant 재시작

### 수동 설치

1. 이 저장소의 `custom_components/run_command` 폴더를 Home Assistant의 `custom_components` 디렉토리에 복사합니다.
2. Home Assistant를 재시작합니다.
3. 설정 → 통합에서 "Run Command"를 검색하여 추가합니다.

## 사용 방법

### 센서 추가

1. 통합 추가 시 다음 정보를 입력합니다:
   - **센서 이름**: 생성될 센서의 이름
   - **실행할 명령어**: 실행할 시스템 명령어 (Jinja2 템플릿 지원)
   - **실행 주기**: 명령어 실행 간격 (초 단위)
   - **결과 형식**: 텍스트 또는 JSON
   - **값 템플릿**: 센서 상태값을 만들기 위한 템플릿 (선택사항)
   - **속성 템플릿**: 추가 속성을 만들기 위한 JSON 형식의 템플릿 (선택사항)

### 센서 설정 수정

1. 설정 → 통합 → Run Command에서 설정하고자 하는 센서 선택
2. 톱니바퀴 아이콘 클릭
3. 설정값 수정 후 저장

### 템플릿 변수

값 템플릿과 속성 템플릿에서 사용 가능한 변수:
- `value`: 명령어 실행 결과 (문자열)
- `json`: JSON으로 파싱된 결과 (결과 형식이 JSON인 경우)

### 예제

#### 기본 텍스트 센서
```yaml
명령어: cat /proc/loadavg
값 템플릿: {{ value.split()[0] }}
```

#### JSON 결과 처리
```yaml
명령어: curl -s http://api.example.com/data
결과 형식: JSON
값 템플릿: {{ json.temperature }}
속성 템플릿: {"humidity": "{{ json.humidity }}", "pressure": "{{ json.pressure }}"}
```

#### 템플릿을 사용한 동적 명령어
```yaml
명령어: echo "현재 온도: {{ states('sensor.temperature') }}°C"
값 템플릿: {{ value | regex_findall('온도: ([\d.]+)') | first }}
```

## 라이센스

MIT License - Pages in Korea (pages.kr)
