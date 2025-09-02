"""
네이버 Direction 5 API 클라이언트

실시간 교통정보를 반영한 정확한 경로 계산 및 ETA 계산을 위한 모듈입니다.
"""

import os
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

# LocationInfo 대신 Tuple[float, float] 사용 (위도, 경도)

logger = logging.getLogger(__name__)

class NaverDirectionClient:
    """네이버 Direction 5 API 클라이언트"""
    
    BASE_URL = "https://maps.apigw.ntruss.com/map-direction/v1/driving"
    
    def __init__(self):
        self.client_id = os.getenv('NAVER_CLIENT_ID')
        self.client_secret = os.getenv('NAVER_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 환경변수가 설정되어야 합니다")
    
    def _get_headers(self) -> Dict[str, str]:
        """API 요청에 필요한 헤더 생성"""
        return {
            'x-ncp-apigw-api-key-id': self.client_id,
            'x-ncp-apigw-api-key': self.client_secret
        }
    
    def _build_request_params(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> Dict[str, str]:
        """Direction 5 API 요청 파라미터 생성"""
        return {
            "start": f"{origin[1]},{origin[0]}",  # 경도,위도 순서
            "goal": f"{destination[1]},{destination[0]}"  # 경도,위도 순서
        }
    
    async def get_driving_time(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> Optional[int]:
        """
        두 지점 간 실제 운전 소요시간 계산
        
        Args:
            origin: 출발지 위치 정보
            destination: 목적지 위치 정보
        
        Returns:
            int: 소요시간 (분), 실패 시 None
        """
        try:
            request_params = self._build_request_params(origin, destination)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.BASE_URL,
                    params=request_params,
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"네이버 API 응답: {json.dumps(data, indent=2, ensure_ascii=False)}")
                        return self._extract_travel_time(data)
                    else:
                        error_text = await response.text()
                        logger.error(f"네이버 Direction API 오류: {response.status}, {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("네이버 Direction API 타임아웃")
            return None
        except Exception as e:
            logger.error(f"네이버 Direction API 호출 오류: {str(e)}")
            return None
    
    def _extract_travel_time(self, api_response: Dict[str, Any]) -> Optional[int]:
        """
        API 응답에서 소요시간 추출
        
        Args:
            api_response: 네이버 Direction API 응답
            
        Returns:
            int: 소요시간 (분), 추출 실패 시 None
        """
        try:
            if api_response.get('code') != 0:
                logger.error(f"API 응답 오류: {api_response.get('message', 'Unknown error')}")
                return None
            
            route = api_response.get('route', {})
            # traoptimal 또는 trafast 경로 정보 확인
            route_data = route.get('traoptimal', route.get('trafast', []))
            
            if not route_data:
                logger.error("경로 정보를 찾을 수 없습니다")
                return None
            
            # 첫 번째 경로의 소요시간 사용 (밀리초 단위)
            duration_ms = route_data[0].get('summary', {}).get('duration', 0)
            
            # 밀리초를 분으로 변환
            duration_minutes = round(duration_ms / 1000 / 60)
            
            logger.debug(f"계산된 소요시간: {duration_minutes}분 (원본: {duration_ms}ms)")
            
            return max(1, duration_minutes)  # 최소 1분
            
        except Exception as e:
            logger.error(f"소요시간 추출 오류: {str(e)}")
            return None
    
    async def batch_calculate_eta(
        self, 
        origins: List[Tuple[float, float]], 
        destination: Tuple[float, float],
        max_concurrent: int = 3
    ) -> List[Tuple[int, Optional[int]]]:
        """
        여러 출발지에서 목적지까지의 ETA를 배치로 계산
        
        Args:
            origins: 출발지 위치 목록
            destination: 공통 목적지
            max_concurrent: 최대 동시 요청 수 (기본 3개, Rate Limiting 고려)
        
        Returns:
            List[Tuple[int, Optional[int]]]: (인덱스, ETA분) 튜플 리스트
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def calculate_single_eta(index: int, origin: Tuple[float, float]) -> Tuple[int, Optional[int]]:
            async with semaphore:
                eta = await self.get_driving_time(origin, destination)
                # API 호출 간격 조정 (Rate Limiting 준수)
                await asyncio.sleep(0.2)
                return (index, eta)
        
        tasks = [
            calculate_single_eta(i, origin) 
            for i, origin in enumerate(origins)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리 및 결과 정리
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"배치 ETA 계산 중 오류: {str(result)}")
                processed_results.append((-1, None))
            else:
                processed_results.append(result)
        
        return processed_results


class ETACalculator:
    """ETA 계산 및 캐싱을 담당하는 클래스"""
    
    def __init__(self, use_mock_data: bool = False, mock_data_path: str = None):
        """
        Args:
            use_mock_data: 목 데이터 사용 여부
            mock_data_path: 목 데이터 파일 경로
        """
        self.use_mock_data = use_mock_data
        self.mock_data = {}
        self.cache = {}  # 간단한 메모리 캐시
        
        if use_mock_data and mock_data_path:
            self._load_mock_data(mock_data_path)
        
        if not use_mock_data:
            self.naver_client = NaverDirectionClient()
    
    def _load_mock_data(self, mock_data_path: str):
        """목 데이터 로드"""
        try:
            with open(mock_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.mock_data = data.get('direction', {})
            logger.info(f"목 데이터 로드 완료: {len(self.mock_data)}개 경로")
        except Exception as e:
            logger.error(f"목 데이터 로드 실패: {str(e)}")
            self.mock_data = {}
    
    def _generate_cache_key(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> str:
        """캐시 키 생성"""
        return f"{origin[1]},{origin[0]}_to_{destination[1]},{destination[0]}"
    
    
    async def calculate_eta(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> int:
        """
        ETA 계산 (네이버 Direction API 사용)
        
        Args:
            origin: 출발지 (위도, 경도)
            destination: 목적지 (위도, 경도)
            
        Returns:
            int: ETA (분)
        """
        cache_key = self._generate_cache_key(origin, destination)
        
        # 캐시 확인
        if cache_key in self.cache:
            logger.debug(f"캐시에서 ETA 반환: {cache_key}")
            return self.cache[cache_key]
        
        # 실제 네이버 API 호출
        eta = await self.naver_client.get_driving_time(origin, destination)
        if eta:
            logger.debug(f"네이버 API에서 ETA 계산: {eta}분")
        
        # Fallback: 거리 기반 계산
        if eta is None:
            import math
            # Haversine 공식으로 거리 계산
            R = 6371  # 지구 반지름 (km)
            lat1, lon1, lat2, lon2 = map(math.radians, [origin[0], origin[1], destination[0], destination[1]])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance_km = R * c
            
            # 평균 30km/h로 ETA 계산
            eta = int((distance_km / 30.0) * 60)
            eta = max(1, eta)  # 최소 1분
            logger.warning(f"Fallback ETA 사용: {eta}분 (거리: {distance_km:.2f}km)")
        
        # 캐시에 저장
        self.cache[cache_key] = eta
        
        return eta
    
    async def batch_calculate_eta(
        self, 
        origins: List[Tuple[float, float]], 
        destination: Tuple[float, float]
    ) -> List[int]:
        """
        배치 ETA 계산
        
        Args:
            origins: 출발지 목록 (위도, 경도) 튜플 리스트
            destination: 공통 목적지 (위도, 경도)
            
        Returns:
            List[int]: 각 출발지의 ETA (분) 리스트
        """
        # 네이버 API를 사용한 배치 계산
        batch_results = await self.naver_client.batch_calculate_eta(origins, destination)
        
        processed_results = []
        for i, eta in enumerate(batch_results):
            if eta is None:
                # Fallback 계산
                eta = await self.calculate_eta(origins[i], destination)
            processed_results.append(eta)
        
        return processed_results