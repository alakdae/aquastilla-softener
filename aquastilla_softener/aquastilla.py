import logging
import pytz
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
    CLOSED = "deviceStateClosed"
    BRINEREFILL = "deviceStateRegenBrineRefill"
    SALTDISSOLVE = "deviceStateRegenSaltDissolve"
    REGENBACKWASH = "deviceStateRegenBackwash"
    BRINECOLLECT = "deviceStateRegenBrineCollect"
    FASTWASH = "deviceStateRegenFastwash"
    OFFLINE = "Offline"

@dataclass(frozen=True)
class AquastillaSoftenerData:
    # Core info
    timestamp: datetime
    uuid: str
    model: str
    state: AquastillaSoftenerState

    # Salt info
    salt_level_percent: int
    salt_days_remaining: int
    salt_days_max: int
    minimum_salt_level_per_days: int

    # Water usage/capacity
    water_available: float
    max_water_capacity: float
    current_water_usage: float
    today_water_usage: float

    # Regeneration
    expected_regeneration_date: datetime
    last_regeneration: datetime
    regen_percentage: float

    # Firmware
    firmware_upgrade_percentage: float
    is_update: bool

    # Modes and flags
    is_online: bool
    service_mode: bool
    water_flow: bool
    vacation_mode: bool

    # Water details
    water_hardness: int
    unit_of_volume: str
    water_hardness_unit: str

    # Flood alarm settings
    flood_continuous_flow_time: int
    flood_threshold: int
    flood_max_flow: int

    # Service info
    service_mode_ending_time: datetime

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
            response_settings = session.get(f"{self._api_base_url}/device/{device['uuid']}/settings", headers=self._get_headers())
            if response_settings.status_code != 200:
                raise Exception(f"Failed to fetch device state: {response_settings.text}")
            data_settings = response_settings.json()
            tz = pytz.timezone(data_settings["timezone"])
            timestamp_correct = tz.localize(datetime.fromisoformat(data["timestamp"].replace("+00:00", "")))
            expected_regeneration_date_correct = tz.localize(datetime.fromisoformat(data["expectedRegenerationDate"].replace("+00:00", "")))
            last_regeneration_correct = tz.localize(datetime.fromisoformat(device["lastRegeneration"].replace("+00:00", "")))
            service_mode_ending_time_correct = tz.localize(datetime.fromisoformat(data_settings["serviceModeEndingTime"].replace("+00:00", "")))
            return AquastillaSoftenerData(
                timestamp=timestamp_correct,
                uuid=data["uuid"],
                model=device["model"]["model"],
                state=AquastillaSoftenerState(data["state"]),
                salt_level_percent=data["saltPercent"],
                salt_days_remaining=data["saltDays"],
                water_available=data["waterLeft"],
                max_water_capacity=data["waterLeftMax"],
                expected_regeneration_date=expected_regeneration_date_correct,
                current_water_usage=data["currentWaterUsage"],
                today_water_usage=data["todayWaterUsage"],
                last_regeneration=last_regeneration_correct,
                is_online=data["isOnline"],
                is_update = data["isUpdate"],
                vacation_mode = data_settings["vacationMode"],
                water_flow = data_settings["waterFlow"],
                service_mode = data_settings["serviceMode"],
                salt_days_max = data["saltDaysMax"],
                regen_percentage = data["regenPercentage"],
                firmware_upgrade_percentage = data["firmwareUpdatePercentage"],
                water_hardness = data_settings["waterHardness"],
                minimum_salt_level_per_days = data_settings["saltAlarmSettings"]["minimumSaltLevelPerDays"],
                flood_continuous_flow_time = data_settings["floodAlarmSettings"]["continuousFlowTime"],
                flood_threshold = data_settings["floodAlarmSettings"]["threshold"],
                flood_max_flow = data_settings["floodAlarmSettings"]["maxFlow"],
                unit_of_volume = data_settings["unitOfVolume"],
                water_hardness_unit = data_settings["waterHardnessUnit"],
                service_mode_ending_time = service_mode_ending_time_correct,
            )

    def close_water_valve(self, device: Dict):
        with requests.Session() as session:
            self._check_token(session)
            url = f"{self._api_base_url}/device/{device['uuid']}/water_flow"
            headers = self._get_headers()
            headers["Content-Type"] = "application/json"
            payload = str(0)
            response = session.post(url, data=payload, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Failed to close water flow valve: {response.status_code} - {response.text}")
    
    def postpone_regeneration(self, device: Dict):
        with requests.Session() as session:
            self._check_token(session)
            url = f"{self._api_base_url}/device/{device['uuid']}/delay_regeneration"
            headers = self._get_headers()
            headers["Content-Type"] = "application/json"
            payload = ""
            response = session.post(url, data=payload, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Failed to postpone regeneration: {response.status_code} - {response.text}")
    
    def force_regeneration(self, device: Dict):
        with requests.Session() as session:
            self._check_token(session)
            url = f"{self._api_base_url}/device/{device['uuid']}/vacation_mode/force_regeneration"
            headers = self._get_headers()
            headers["Content-Type"] = "application/json"
            payload = ""
            response = session.post(url, data=payload, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Failed to force regeneration: {response.status_code} - {response.text}")
    
    def set_vacation_mode(self, device: Dict, value: int):
        with requests.Session() as session:
            self._check_token(session)
            url = f"{self._api_base_url}/device/{device['uuid']}/vacation_mode"
            headers = self._get_headers()
            headers["Content-Type"] = "application/json"
            payload = str(value)
            response = session.post(url, data=payload, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Failed to set vacation mode: {response.status_code} - {response.text}")
    
