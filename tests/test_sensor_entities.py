"""Tests for Nature Remo sensor entities."""

from typing import Any

from custom_components.nature_remo.sensor import (
    NatureRemoBatteryDeteriorationSensor,
    NatureRemoBatteryLevelSensor,
    NatureRemoBatteryPowerSensor,
    NatureRemoEnergySensor,
    NatureRemoHumiditySensor,
    NatureRemoIlluminanceSensor,
    NatureRemoSolarPowerSensor,
    NatureRemoTemperatureSensor,
)


class FakeCoordinator:
    """Minimal coordinator test double."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data


def test_device_sensor_unique_ids_are_sensor_specific() -> None:
    device = {
        "id": "device-1",
        "name": "Living Room",
        "newest_events": {"te": {"val": 21.5}, "hu": {"val": 55}, "il": {"val": 120}},
    }
    coordinator = FakeCoordinator({"devices": {"device-1": device}})

    assert NatureRemoTemperatureSensor(coordinator, device).unique_id == "device-1-temperature"  # type: ignore[arg-type]
    assert NatureRemoHumiditySensor(coordinator, device).unique_id == "device-1-humidity"  # type: ignore[arg-type]
    assert NatureRemoIlluminanceSensor(coordinator, device).unique_id == "device-1-illuminance"  # type: ignore[arg-type]


def test_device_sensor_native_values_follow_coordinator_data() -> None:
    device = {
        "id": "device-1",
        "name": "Living Room",
        "newest_events": {"te": {"val": 21.5}},
    }
    coordinator = FakeCoordinator({"devices": {"device-1": device}})
    sensor = NatureRemoTemperatureSensor(coordinator, device)  # type: ignore[arg-type]

    assert sensor.native_value == 21.5

    coordinator.data["devices"]["device-1"]["newest_events"]["te"]["val"] = 22.5

    assert sensor.native_value == 22.5


def test_cumulative_energy_sensor_calculates_from_coordinator_data() -> None:
    appliance = {
        "id": "appliance-1",
        "nickname": "Meter",
        "device": {"id": "device-1", "name": "Remo E"},
    }
    coordinator = FakeCoordinator(
        {
            "appliances": {
                "appliance-1": {
                    **appliance,
                    "smart_meter": {
                        "echonetlite_properties": [
                            {"epc": 224, "val": 100},
                            {"epc": 211, "val": 2},
                            {"epc": 225, "val": 1},
                        ]
                    },
                }
            }
        }
    )
    sensor = NatureRemoEnergySensor(coordinator, appliance)  # type: ignore[arg-type]

    assert sensor.available
    assert sensor.native_value == 20

    coordinator.data["appliances"]["appliance-1"]["smart_meter"]["echonetlite_properties"][0][
        "val"
    ] = 110

    assert sensor.native_value == 22


def test_battery_and_solar_sensors_parse_echonet_values() -> None:
    device = {"id": "device-1", "name": "Remo E"}
    battery = {
        "id": "battery-1",
        "nickname": "Battery",
        "type": "EL_STORAGE_BATTERY",
        "device": device,
        "properties": [
            {"epc": "d3", "val": "ffffffd6"},
            {"epc": "e4", "val": "5a"},
            {"epc": "e5", "val": "64"},
        ],
    }
    solar = {
        "id": "solar-1",
        "nickname": "Solar",
        "type": "EL_SOLAR_POWER",
        "device": device,
        "properties": [{"epc": "e0", "val": "12c"}],
    }
    coordinator = FakeCoordinator(
        {"echonetlite_appliances": {"battery-1": battery, "solar-1": solar}}
    )

    battery_power = NatureRemoBatteryPowerSensor(coordinator, battery)  # type: ignore[arg-type]
    battery_level = NatureRemoBatteryLevelSensor(coordinator, battery)  # type: ignore[arg-type]
    battery_deterioration = NatureRemoBatteryDeteriorationSensor(
        coordinator, battery
    )  # type: ignore[arg-type]
    solar_power = NatureRemoSolarPowerSensor(coordinator, solar)  # type: ignore[arg-type]

    assert battery_power.unique_id == "battery-1-battery-power"
    assert battery_power.native_value == -42
    assert battery_level.native_value == 90
    assert battery_level.native_unit_of_measurement == "%"
    assert battery_deterioration.native_value == 100
    assert solar_power.native_value == 300

    coordinator.data["echonetlite_appliances"].pop("battery-1")
    assert not battery_level.available
    assert battery_level.native_value is None
