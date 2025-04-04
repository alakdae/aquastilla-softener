import logging
from enum import Enum, IntEnum
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
try:
    from zoneinfo import ZoneInfo
except:
    from backports.zoneinfo import ZoneInfo

import requests

logger = logging.getLogger(__name__)


DEFAULT_API_BASE_URL = "https://backend.waterlife.pl:15880"
DEFAULT_USER_AGENT = "okhttp/4.9.1"


class AquastillaSoftenerState(str, Enum):
    SOFTENING = "deviceStateSoftening"
    OFFLINE = "Offline"
    

@dataclass(frozen=True)
class AquastillaSoftenerData:
    timestamp: datetime
    uuid: str
    model: str
    state: AquastillaSoftenerState
    salt_level_percent: int
    salt_days_remaining: int
    water_available: float
    max_water_capacity: float
    expected_regeneration_date: datetime
    current_water_usage: float
    today_water_usage: float
    last_regeneration: datetime

    @property
    def water_available_liters(self) -> float:
        return round(self.water_available * 1000, 2)

    @property
    def max_water_capacity_liters(self) -> float:
        return round(self.max_water_capacity * 1000, 2)

    @property
    def current_water_usage_liters(self) -> float:
        return round(self.current_water_usage * 1000, 2)
    
    @property
    def today_water_usage_liters(self) -> float:
        return round(self.today_water_usage * 1000, 2)

class AquastillaSoftener:
    def __init__(
        self, email: str, password: str, api_base_url: str = DEFAULT_API_BASE_URL, user_agent: str = DEFAULT_USER_AGENT
    ):
        self._email: str = email
        self._password: str = password
        self._api_base_url: str = api_base_url
        self._user_agent: str = user_agent
        self._token: Optional[str] = None
        self._token_expiration: Optional[datetime] = None

    def _check_token(self, session: requests.Session):
        if self._token is None or (self._token_expiration and datetime.now(timezone.utc) > self._token_expiration):
            self._update_token(session)

    def _update_token(self, session: requests.Session):
        response = session.post(
            f"{self._api_base_url}/login",
            json={"emailOrPhone": self._email, "password": self._password},
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.text}")
        response_data = response.json()
        self._token = response_data["jwt"]
        self._token_expiration = datetime.fromisoformat(response_data["expirationDate"]).replace(tzinfo=timezone.utc)

    def _get_headers(self) -> Dict[str, str]:
        if not self._token:
            raise Exception("Token not available. Authenticate first.")
        return {"Authorization": f"Bearer {self._token}"}

    def list_devices(self) -> list[Dict]:
        with requests.Session() as session:
            self._check_token(session)
            response = session.get(f"{self._api_base_url}/device/all", headers=self._get_headers())
            if response.status_code != 200:
                raise Exception(f"Failed to fetch devices: {response.text}")
            return response.json()

    def get_device_data(self, device: Dict) -> AquastillaSoftenerData:
        with requests.Session() as session:
            self._check_token(session)
            response = session.get(f"{self._api_base_url}/device/{device['uuid']}/state", headers=self._get_headers())
            if response.status_code != 200:
                raise Exception(f"Failed to fetch device state: {response.text}")
            data = response.json()
            return AquastillaSoftenerData(
                timestamp=datetime.fromisoformat(data["timestamp"]),
                uuid=data["uuid"],
                model=device["model"]["model"],
                state=AquastillaSoftenerState(data["state"]),
                salt_level_percent=data["saltPercent"],
                salt_days_remaining=data["saltDays"],
                water_available=data["waterLeft"],
                max_water_capacity=data["waterLeftMax"],
                expected_regeneration_date=datetime.fromisoformat(data["expectedRegenerationDate"]),
                current_water_usage=data["currentWaterUsage"],
                today_water_usage=data["todayWaterUsage"],
                last_regeneration=datetime.fromisoformat(device["lastRegeneration"]),
            )

