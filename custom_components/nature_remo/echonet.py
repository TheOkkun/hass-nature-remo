"""Helpers for Nature Remo ECHONET Lite smart meter properties."""

from collections.abc import Iterable, Mapping
from typing import Any

EPC_COEFFICIENT = 211
EPC_CUMULATIVE_CONSUMED_ENERGY = 224
EPC_CUMULATIVE_ENERGY_UNIT = 225
EPC_CUMULATIVE_RETURNED_ENERGY = 227
EPC_MEASURED_INSTANTANEOUS_POWER = 231
EPC_BATTERY_INSTANTANEOUS_POWER = 211
EPC_BATTERY_STATE_OF_CHARGE = 228
EPC_BATTERY_DETERIORATION = 229
EPC_SOLAR_INSTANTANEOUS_POWER = 224

CUMULATIVE_ENERGY_UNIT_TABLE: dict[int, float] = {
    0: 1,
    1: 0.1,
    2: 0.01,
    3: 0.001,
    4: 0.0001,
    10: 10,
    11: 100,
    12: 1000,
}


def parse_echonet_properties(
    properties: Iterable[Mapping[str, Any]],
    *,
    hex_values: bool = False,
    signed_epcs: Iterable[int] = (),
) -> dict[int, float]:
    """Parse Nature Remo ECHONET Lite properties by EPC code."""
    signed_epcs = set(signed_epcs)
    parsed: dict[int, float] = {}
    for prop in properties:
        raw_epc = prop["epc"]
        if isinstance(raw_epc, str):
            try:
                epc = int(raw_epc)
            except ValueError:
                epc = int(raw_epc, 16)
        else:
            epc = int(raw_epc)

        raw_value = prop["val"]
        value = (
            float(int(raw_value, 16))
            if hex_values and isinstance(raw_value, str)
            else float(raw_value)
        )
        if epc in signed_epcs and value >= 2**31:
            value -= 2**32
        parsed[epc] = value
    return parsed


def has_epc(properties: Mapping[int, float], epc: int) -> bool:
    """Return whether an EPC code exists in parsed properties."""
    return epc in properties


def calculate_cumulative_energy(properties: Mapping[int, float], epc: int) -> float | None:
    """Calculate cumulative energy in kWh for an EPC code."""
    if epc not in properties:
        return None

    value = properties[epc]
    coefficient = properties.get(EPC_COEFFICIENT, 1)
    unit_code = int(properties.get(EPC_CUMULATIVE_ENERGY_UNIT, 0))
    unit = CUMULATIVE_ENERGY_UNIT_TABLE.get(unit_code, 1)
    return value * coefficient * unit
