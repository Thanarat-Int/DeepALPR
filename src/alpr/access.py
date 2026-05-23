"""Access-control decision logic.

When the pipeline reads a plate, AccessController checks it against the
blacklist and the registered-vehicle whitelist and returns a decision:

    denied   -- plate is on the blacklist
    granted  -- plate is a registered, active vehicle
    alert    -- plate is unknown / unregistered  (operator should verify)
"""
from dataclasses import dataclass


@dataclass
class AccessResult:
    decision: str                       # granted | denied | alert
    reason: str
    owner_name: str | None = None
    vehicle_type: str | None = None
    brand_model: str | None = None
    vehicle_year: int | None = None
    registered_color: str | None = None  # color the owner declared at signup
    registered_province: str | None = None


class AccessController:
    def __init__(self, db):
        self.db = db

    def evaluate(self, plate: str) -> AccessResult:
        blacklisted = self.db.find_blacklist(plate)
        if blacklisted:
            return AccessResult(
                "denied", blacklisted.get("reason") or "Blacklisted vehicle")

        vehicle = self.db.find_registered(plate)
        if vehicle:
            vtype = vehicle.get("vehicle_type", "vehicle")
            return AccessResult(
                "granted", f"Registered {vtype}",
                owner_name=vehicle.get("owner_name"),
                vehicle_type=vtype,
                brand_model=vehicle.get("brand_model"),
                vehicle_year=vehicle.get("vehicle_year"),
                registered_color=vehicle.get("color"),
                registered_province=vehicle.get("province"))

        return AccessResult("alert", "Unregistered vehicle")
