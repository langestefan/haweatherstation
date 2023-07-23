"""Main module"""

import logging

import yaml

from .weatherstation import WeatherStation

_LOGGER = logging.getLogger(__name__)


def init_logger():
    """Initialize python logger."""
    logging.basicConfig(level=logging.DEBUG)
    fmt = "%(asctime)s %(levelname)s (%(threadName)s) " + "[%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # stdout handler
    logging.getLogger().handlers[0].setFormatter(
        logging.Formatter(fmt, datefmt=datefmt)
    )


def main():
    """Main function"""

    # init logger
    init_logger()

    # load config
    with open("haweatherstation/config.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
        _LOGGER.debug("Loaded config: \n%s", config)

    # create weather station
    weather_station = WeatherStation(
        station_id=config["station_id"],
        station_model=config["station_model"],
        entity_id=config["entity_id"],
        usb_path=config["usb_path"],
    )

    # run the weather station
    for weather_obj in weather_station.run_loop():
        _LOGGER.debug("Weather data: %s", weather_obj)


if __name__ == "__main__":
    main()
