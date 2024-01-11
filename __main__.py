"""Main module"""

import logging

import yaml

from .hassapi import HassAPI, HassEntity
from .weatherstation import WeatherStation

_LOGGER = logging.getLogger(__name__)

SENSOR = "sensor"
BINARY_SENSOR = "binary_sensor"


def init_logger(log_level=logging.DEBUG):
    """Initialize python logger.

    :param log_level: The log level to run the entire application with.
    """
    logging.basicConfig(level=log_level)
    fmt = "%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # stdout handler
    logging.getLogger().handlers[0].setFormatter(
        logging.Formatter(fmt, datefmt=datefmt)
    )


def main():
    """Main function"""

    # load config
    with open("haweatherstation/config.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
        _LOGGER.debug("Loaded config: \n%s", config)

    # load secrets
    with open("haweatherstation/secrets.yaml", "r", encoding="utf-8") as file:
        secrets = yaml.safe_load(file)
        _LOGGER.debug("Loaded secrets: REDACTED")

    # init logger
    init_logger(log_level=config["log_level"])
    _LOGGER.info("Application initialized.")

    # create weather station
    weather_station = WeatherStation(
        station_id=config["station_id"],
        station_model=config["station_model"],
        usb_path=config["usb_path"],
    )
    _LOGGER.info("Weather station created.")

    # create hass api
    api = HassAPI(
        hass_url=config["hass_url"],
        token=secrets["hass_token"],
    )
    _LOGGER.info("Hass API online: %s", api.online)

    # create hass entities
    sensor_entity_prefix = f"{SENSOR}.{config['entity_id']}_"
    binary_sensor_entity_prefix = f"{BINARY_SENSOR}.{config['entity_id']}_"
    temperature = HassEntity(
        api=api,
        entity_id=sensor_entity_prefix + "temperature",
        unit_of_measurement="°C",
        icon="mdi:thermometer",
        dtype=float,
    )
    humidity = HassEntity(
        api=api,
        entity_id=sensor_entity_prefix + "humidity",
        unit_of_measurement="%",
        icon="mdi:water-percent",
        dtype=int,
    )
    wind_max_speed = HassEntity(
        api=api,
        entity_id=sensor_entity_prefix + "wind_speed_max",
        unit_of_measurement="m/s",
        icon="mdi:weather-windy",
        dtype=float,
    )
    wind_avg_speed = HassEntity(
        api=api,
        entity_id=sensor_entity_prefix + "wind_speed_avg",
        unit_of_measurement="m/s",
        icon="mdi:weather-windy",
        dtype=float,
    )
    wind_direction = HassEntity(
        api=api,
        entity_id=sensor_entity_prefix + "wind_direction",
        unit_of_measurement="°",
        icon="mdi:compass",
        dtype=int,
    )
    rain = HassEntity(
        api=api,
        entity_id=sensor_entity_prefix + "rain",
        unit_of_measurement="mm",
        icon="mdi:weather-rainy",
        dtype=float,
    )
    battery_ok = HassEntity(
        api=api,
        entity_id=binary_sensor_entity_prefix + "battery_ok",
        icon="mdi:battery-heart",
        dtype=str,
    )

    # build mapping dict
    mapping = {
        "temperature": temperature,
        "humidity": humidity,
        "wind_speed_max": wind_max_speed,
        "wind_speed_avg": wind_avg_speed,
        "wind_direction": wind_direction,
        "rain": rain,
        "battery_ok": battery_ok,
    }

    # run the weather station
    packet_count = 0
    for weather_obj in weather_station.run_loop():
        packet_count += 1
        _LOGGER.debug("Received RF frame %s. Updating weather station state objects.", packet_count)

        # update the hass entities
        for key, value in weather_obj.__dict__.items():
            if key in mapping:
                # convert True and False to on and off
                if key == "battery_ok":
                    value = "on" if value else "off"
                _LOGGER.debug("Updating entity %s with value %s", key, value)
                mapping[key].update(state=value)


if __name__ == "__main__":
    main()
