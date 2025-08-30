# MockNaverMapClient \사용 가이드

## 📋 문서 개요
본 문서는 네이버 지도 API와의 실제 연동 없이, 사전에 정의된 Mock 데이터를 사용하여 위치 정보 조회(`geocode`) 및 경로 탐색(`direction`) 기능을 테스트하고 개발할 수 있도록 돕는 `MockNaverMapClient`의 사용 방법을 설명합니다.

실제 API 호출에 따른 비용과 시간 제약을 해결하고, 안정적인 통합 테스트 환경을 구축하는 것을 목표로 합니다.

## 🎯 핵심 기능

`MockNaverMapClient`는 실제 네이버 지도 API 클라이언트와 동일한 인터페이스를 제공하지만, 네트워크 호출 대신 로컬에 저장된 `naver_map_api_dataset.json` 파일을 읽어 미리 정의된 결과를 반환합니다.

- `get_geocode(query: str)`: 주소 문자열을 입력받아 해당하는 좌표 정보가 포함된 API 응답을 반환합니다.
- `get_direction(start: str, goal: str)`: 출발지와 목적지 좌표 문자열을 입력받아 해당하는 경로 정보가 포함된 API 응답을 반환합니다.

## 💾 Mock 데이터셋 구조

Mock 데이터는 `tests/mock_data/naver_map_api_dataset.json` 파일에 **입력 기반 데이터셋** 형식으로 저장되어 있습니다. API 요청의 핵심 입력값(주소, 경로)을 Key로, 해당 API의 전체 응답을 Value로 가집니다.

```json
{
  "geocode": {
    "경기도 성남시 분당구 불정로 6": { "status": "OK", ... },
    "서울시청": { "status": "OK", ... }
  },
  "direction": {
    "127.1058342,37.359708_to_129.075986,35.179470": { "code": 0, ... },
    "126.978652,37.566826_to_127.1052133,37.3595122": { "code": 0, ... }
  }
}
```

## 🚀 사용 방법 및 테스트 예제

다음은 Python 코드에서 `MockNaverMapClient`를 초기화하고 사용하는 방법에 대한 예시입니다.

### 1. 클라이언트 초기화

`homecare_matching.app.utils.naver_map` 모듈에서 `MockNaverMapClient`를 import하여 인스턴스를 생성합니다. 데이터셋 파일 경로는 기본값으로 설정되어 있습니다.

```python
from homecare_matching.app.utils.naver_map import MockNaverMapClient

# Mock 클라이언트 인스턴스 생성
map_client = MockNaverMapClient()
```

### 2. `get_geocode` 사용 예제

데이터셋에 Key로 정의된 주소 문자열을 `query` 파라미터로 전달하여 `get_geocode` 함수를 호출합니다.

```python
# 테스트 예제 1: "경기도 성남시 분당구 불정로 6" 주소로 지오코딩 정보 요청
query_address = "경기도 성남시 분당구 불정로 6"
geocode_response = map_client.get_geocode(query_address)

if geocode_response:
    print(f"'-- 질의 주소: {query_address}'에 대한 응답 --")
    # 응답에서 도로명 주소와 좌표 정보 추출
    road_address = geocode_response.get("addresses", [{}])[0].get("roadAddress")
    coords_x = geocode_response.get("addresses", [{}])[0].get("x")
    coords_y = geocode_response.get("addresses", [{}])[0].get("y")
    print(f"도로명 주소: {road_address}")
    print(f"좌표: x={coords_x}, y={coords_y}")
else:
    print(f"'-- 질의 주소: {query_address}'에 대한 mock 데이터를 찾을 수 없습니다. --")

# 출력 결과:
# '-- 질의 주소: 경기도 성남시 분당구 불정로 6'에 대한 응답 --
# 도로명 주소: 경기도 성남시 분당구 불정로 6
# 좌표: x=127.1052133, y=37.3595122
```

### 3. `get_direction` 사용 예제

데이터셋에 Key로 정의된 `"{start}_to_{goal}"` 형식의 문자열에 맞춰 `start`와 `goal` 좌표를 전달하여 `get_direction` 함수를 호출합니다.

```python
# 테스트 예제 2: 정의된 경로로 소요 시간 정보 요청
start_coords = "127.1058342,37.359708"
goal_coords = "129.075986,35.179470"
direction_response = map_client.get_direction(start_coords, goal_coords)

if direction_response:
    print(f"\n'-- 경로: {start_coords} -> {goal_coords}'에 대한 응답 --")
    # 응답에서 경로 요약 정보 추출
    summary = direction_response.get("route", {}).get("trafast", [{}])[0].get("summary", {})
    duration_ms = summary.get("duration")
    toll_fare = summary.get("tollFare")
    print(f"예상 소요 시간(ms): {duration_ms}")
    print(f"예상 통행료(원): {toll_fare}")
else:
    print(f"\n'-- 경로: {start_coords} -> {goal_coords}'에 대한 mock 데이터를 찾을 수 없습니다. --")

# 출력 결과:
# '-- 경로: 127.1058342,37.359708 -> 129.0T75986,35.179470'에 대한 응답 --
# 예상 소요 시간(ms): 13918021
# 예상 통행료(원): 18300
```

## ➕ 새로운 테스트 데이터 추가 방법

새로운 테스트 시나리오가 필요한 경우, `tests/mock_data/naver_map_api_dataset.json` 파일을 직접 수정하여 새로운 "입력:응답" 쌍을 추가할 수 있습니다.

1.  **지오코딩 데이터 추가**: `geocode` 객체 내부에 `{ "새로운 주소": { ...응답... } }` 형식으로 추가합니다.
2.  **경로 데이터 추가**: `direction` 객체 내부에 `{ "{start}_to_{goal}": { ...응답... } }` 형식으로 추가합니다.
