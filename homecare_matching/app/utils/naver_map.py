import json
from typing import Dict, Any, Optional

class MockNaverMapClient:
    _dataset = None

    def __init__(self, dataset_path: str = "tests/mock_data/naver_map_api_dataset.json"):
        if MockNaverMapClient._dataset is None:
            # 파일 읽을 때 UTF-8 인코딩 명시
            with open(dataset_path, 'r', encoding='utf-8') as f:
                MockNaverMapClient._dataset = json.load(f)

    def get_geocode(self, query: str) -> Optional[Dict[str, Any]]:
        """주소(query)를 키로 사용하여 mock 지오코딩 응답을 반환합니다."""
        return self._dataset.get("geocode", {}).get(query)

    def get_direction(self, start: str, goal: str) -> Optional[Dict[str, Any]]:
        """출발지와 목적지 좌표를 키로 사용하여 mock 경로 탐색 응답을 반환합니다."""
        key = f"{start}_to_{goal}"
        return self._dataset.get("direction", {}).get(key)
