"""Weather station module"""

import json
import logging
import subprocess
from dataclasses import InitVar, dataclass, field
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


@dataclass()
class WeatherStation:
    """Dataclass for the weather station

    :param station_id: The id of the weather station
    :param model_type: The model type of the weather station
    :param entity_id: The entity id of the weather station
    :param usb_path: The path to the usb device
    """

    station_id: int
    station_model: str
    entity_id: str
    usb_path: str
    _command: str = field(init=False)

    def __post_init__(self):
        self._command = f"rtl_433 -c {self.usb_path} -f 868.3M -F json"

    def run_loop(self) -> str:
        """Main loop for the weather station

        :return: The weatherstation output data
        """
        with subprocess.Popen(
            self._command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
        ) as proc:
            while True:
                # returns None while subprocess is running
                retcode = proc.poll()
                if retcode is not None:
                    break

                # decode the line
                line = proc.stdout.readline()
                line = line.decode("utf-8").strip()

                # load the line as json
                if not line.startswith("{"):
                    continue
                try:
                    raw_data: dict = json.loads(line)
                except json.JSONDecodeError:
                    # Log the line
                    _LOGGER.error("Error decoding line: %s", line)
                    continue

                # Check if the line is from the correct station
                st_id = raw_data.get("id")
                model = raw_data.get("model")
                if st_id != self.station_id or model != self.station_model:
                    _LOGGER.debug("Wrong station id or model: \n%s", line)
                    continue

                # create the weather data object
                data_obj = WeatherData(raw_data=raw_data)
                yield data_obj


@dataclass()
class WeatherData:
    """Dataclass for the weather station data

    Example data from the weather station:

    {
       "time":"2023-07-23 00:40:40",
       "model":"Bresser-5in1",
       "id":176,
       "battery_ok":1,
       "temperature_C":14.600,
       "humidity":91,
       "wind_max_m_s":0.800,
       "wind_avg_m_s":1.100,
       "wind_dir_deg":180.000,
       "rain_mm":20.000,
       "mic":"CHECKSUM"
    }

    """

    raw_data: InitVar[dict]
    temperature: float = field(init=False)
    humidity: int = field(init=False)
    wind_speed_avg: float = field(init=False)
    wind_speed_max: float = field(init=False)
    wind_direction: int = field(init=False)
    rain: float = field(init=False)
    battery_ok: bool = field(init=False)
    date_time: datetime = field(init=False)

    def __post_init__(self, raw_data: dict):
        self.temperature = float(raw_data.get("temperature_C"))
        self.humidity = int(raw_data.get("humidity"))
        self.wind_speed_avg = float(raw_data.get("wind_avg_m_s"))
        self.wind_speed_max = float(raw_data.get("wind_max_m_s"))
        self.wind_direction = int(raw_data.get("wind_dir_deg"))
        self.rain = float(raw_data.get("rain_mm"))
        self.battery_ok = bool(raw_data.get("battery_ok"))
        self.date_time = datetime.strptime(raw_data.get("time"), "%Y-%m-%d %H:%M:%S")
