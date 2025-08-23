# Run Command Integration for Home Assistant

웹 UI에서 설정 가능한 command_line 센서를 생성하는 Home Assistant 통합입니다.

**제작자**: Pages in Korea (pages.kr)

## 기능

- 웹 UI를 통한 간편한 센서 생성
- Jinja2 템플릿을 사용한 동적 명령어 실행
- 실행 주기 설정 가능
- 실행 제한 시간 설정 (최대 10분)
- 값 템플릿을 통한 결과 가공
- 속성 템플릿을 통한 커스텀 속성 생성
- 센서 설정 수정 기능
- 측정 단위 설정
- 멀티라인 코드 에디터 지원
- 기존값 유지 옵션 (오류 발생 시 이전 값 유지)

## 설치

### HACS를 통한 설치 (권장)

1. HACS에서 사용자 정의 저장소로 추가: `https://github.com/pageskr/ha-run-command`
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
   - **실행 제한 시간**: 명령어 실행 최대 대기 시간 (1-600초, 기본값: 60초)
   - **실행 주기**: 명령어 실행 간격 (초 단위)
   - **값 템플릿**: 센서 상태값을 만들기 위한 템플릿 (선택사항)
   - **속성 템플릿**: 추가 속성을 만들기 위한 JSON 형식의 템플릿 (선택사항)
   - **측정 단위**: 센서의 측정 단위 (선택사항)
   - **기존값 유지**: 오류 발생 시 이전 값 유지 여부

### 센서 설정 수정

1. 설정 → 통합 → Run Command에서 설정하고자 하는 센서 선택
2. 톱니바퀴 아이콘 클릭
3. 설정값 수정 후 저장

### 템플릿 변수

값 템플릿과 속성 템플릿에서 사용 가능한 변수:
- `value`: 명령어 실행 결과 전체 텍스트 (문자열)
- `value_json`: JSON으로 파싱된 객체 (JSON 형식이 아닌 경우 None)

### 센서 속성

- `last_update`: 마지막 명령어 실행 시간 (ISO 형식)
- `last_error`: 마지막 오류 메시지 (오류 발생 시)
- `template_error`: 템플릿 렌더링 오류 메시지 (템플릿 오류 시)
- `template_result`: 템플릿 결과가 false/none/unknown/unavailable인 경우 표시
- 사용자 정의 속성: 속성 템플릿으로 정의한 속성들

### 기존값 유지 기능

"기존값 유지" 옵션을 활성화하면:
- 명령어 실행 실패 시 센서 값이 이전 값으로 유지됨
- 값 템플릿 결과가 `false`, `none`, `unknown`, `unavailable`인 경우 이전 값 유지
- 템플릿 렌더링 오류 시 이전 값 유지
- 속성값들은 "기존값 유지" 옵션과 무관하게 항상 업데이트됨

### 예제

#### 기본 텍스트 센서
```yaml
명령어: cat /proc/loadavg
값 템플릿: {{ value.split()[0] }}
측정 단위: load
```

#### JSON 결과 처리
```yaml
명령어: curl -s http://api.example.com/data
값 템플릿: {{ value_json.temperature }}
속성 템플릿: {"humidity": "{{ value_json.humidity }}", "pressure": "{{ value_json.pressure }}", "raw_data": "{{ value }}"}
측정 단위: °C
```

#### 템플릿을 사용한 동적 명령어
```yaml
명령어: echo "현재 온도: {{ states('sensor.temperature') }}°C"
값 템플릿: {{ value | regex_findall('온도: ([\d.]+)') | first }}
측정 단위: °C
```

#### 시스템 상태 확인
```yaml
명령어: df -h / | tail -n 1
값 템플릿: {{ value.split()[4] }}
속성 템플릿: {"total": "{{ value.split()[1] }}", "used": "{{ value.split()[2] }}", "available": "{{ value.split()[3] }}"}
측정 단위: %
```

#### 장시간 실행 명령어
```yaml
명령어: /path/to/long-running-script.sh
실행 제한 시간: 300
실행 주기: 3600
```

#### 기존값 유지 예제
```yaml
명령어: curl -s --max-time 5 http://api.example.com/status
값 템플릿: {{ value_json.status if value_json else "unknown" }}
기존값 유지: 체크
측정 단위: status
```
위 설정에서 API 호출이 실패하거나 "unknown"을 반환하면 센서의 이전 상태값이 유지됩니다.

## 라이센스

MIT License - Pages in Korea (pages.kr)
