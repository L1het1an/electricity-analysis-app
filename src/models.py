import hashlib
import hmac

class User:
    "@property def users_id(self) -> int: return self._users_id"
    def __init__(
        self, 
        users_id: int, 
        users_name: str, 
        password_hash: str, 
        role: str, 
        home_ids: list[int] | None = None
    ) -> None:
        self._users_id = users_id
        self.users_name = users_name
        self.__password_hash = password_hash
        self.role = role
        self.home_ids: list[int] = list(home_ids) if home_ids is not None else []

    def is_admin(self) -> bool:
        return self.role == "Admin"

    def can_access_home(self, home_id: int) -> bool:
        return self.is_admin() or home_id in self.home_ids

    def verify_password(self, password: str) -> bool:
        computed_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(self.__password_hash, computed_hash)

class Household:
    def __init__(
        self, 
        home_id: int
    ) -> None:
        self.home_id = home_id

class Appliance:
    def __init__(
        self, 
        appliance_id: int, 
        appliance_name: str, 
    ) -> None:
        self.appliance_id = appliance_id
        self.appliance_name = appliance_name

class Measurement:
    def __init__(
        self, 
        measurement_id: int, 
        home_id: int, 
        appliance_id: int, 
        energy_consumption: float,
        time: str,
        date: str,
        outdoor_temperature: float,
        season: str,
        household_size: int
    ) -> None:
        self.measurement_id = measurement_id
        self.home_id = home_id
        self.appliance_id = appliance_id
        self.energy_consumption = energy_consumption
        self.time = time
        self.date = date
        self.outdoor_temperature = outdoor_temperature
        self.season = season
        self.household_size = household_size