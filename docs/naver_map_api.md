# 위치정보 조회 API
## 요청 방법
```bash
curl --location --request GET 'https://maps.apigw.ntruss.com/map-geocode/v2/geocode?query=분당구 불정로 6' \
--header 'x-ncp-apigw-api-key-id: {API Key ID}' \
--header 'x-ncp-apigw-api-key: {API Key}' \
--header 'Accept: application/json'
```

## 응답 바디
필드	타입	필수 여부	설명
status	String	-	응답 코드
meta	Object	-	메타 데이터
meta.totalCount	Number	-	응답 결과 개수
meta.page	Number	-	현재 페이지 번호
meta.count	Number	-	페이지 내 결과 개수
addresses	Array	-	주소 정보 목록
errorMessage	String	-	오류 메시지
500 오류(알 수 없는 오류) 발생 시에만 표시

### 응답 바디 -  addresses
응답 바디 중 우리에게 중요한 정보는 addresses임
addresses 중 `englishAddress`와 `distance`는 model을 보면 알 수 있듯이 우리 locationInfo에 필요한 정보가 아님

필드	타입	필수 여부	설명
roadAddress	String	-	도로명 주소
jibunAddress	String	-	지번 주소
englishAddress	String	-	영어 주소
addressElements	Array	-	주소 구성 요소 정보
x	String	-	X 좌표(경도)
y	String	-	Y 좌표(위도)
distance	Double	-	중심 좌표로부터의 거리(m)

# Direction 5 API
추후 CH기법이나 ETA 계산에 사용될 API로 출발지와 도착지를 입력했을 때 이용에 소요되는 시간을 계산할 수 있음

## 요청 방법
```bash
curl --location --request GET 'https://maps.apigw.ntruss.com/map-direction/v1/driving?goal=129.075986%2C35.179470&start=127.1058342%2C37.359708' \
--header 'x-ncp-apigw-api-key-id: {API Key ID}' \
--header 'x-ncp-apigw-api-key: {API Key}'
```

## 응답 바디
필드	타입	필수 여부	설명
code	Integer	-	응답 코드
message	String	-	응답 메시지
currentDateTime	String	-	경로 조회 일시(yyyy-MM-ddTHH:mm:ss)
route	Object	-	경로 조회 결과
route.{option}	Array	-	요청한 옵션에 따른 경로 정보
trafast | tracomfort | traoptimal | traavoidtoll | traavoidcaronly
trafast: 실시간 빠른 길
tracomfort: 실시간 편한 길
traoptimal: 실시간 최적
traavoidtoll: 무료 우선
traavoidcaronly: 자동차 전용 도로 회피 우선
