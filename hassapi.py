"""Home Assistant API interface. Handles the communication with the Home Assistant API."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

from requests import Response, get, post

_LOGGER = logging.getLogger(__name__)


@dataclass
class HassAPI:
    """Home Assistant API interface."""

    hass_url: str
    token: str
    timeout: int = field(default=5)
    _headers: dict = field(default_factory=dict)

    def __post_init__(self):
        self._headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
        }

        # check if the API is online
        if not self.online:
            raise ConnectionError("Home Assistant API is not reachable.")

    @property
    def url(self) -> str:
        """Return the url to the Home Assistant API."""
        return urljoin(self.hass_url, "api/")

    @property
    def headers(self) -> dict:
        """Return the headers to the Home Assistant API."""
        return self._headers

    @property
    def online(self) -> bool:
        """Return True if the Home Assistant API is online."""
        response: Response = get(self.url, headers=self.headers, timeout=self.timeout)
        _LOGGER.debug("Home Assistant API online: %s", response.ok)
        return response.ok

    def get_entity_state(self, entity_id: str) -> dict:
        """Get the state object for specified entity_id. Returns None if entity not found.

        :param entity_id: The entity_id to get the state object for.
        :return: The state object for the specified entity_id.
        """
        url = self._format_entity_url(entity_id)
        response: Response = get(url, headers=self.headers, timeout=self.timeout)

        # if we receive a 404 the entity does not exist and we can't continue
        if response.status_code == 404:
            raise ValueError(f"Entity {entity_id} not found.")
        if not response.ok:
            raise ConnectionError(
                f"Error while getting entity {entity_id}: {response.reason}"
            )
        return response

    def post_entity_state(self, entity_id: str, state: dict) -> Response:
        """Post the state object for specified entity_id.

        Example:

        url = "http://localhost:8123/api/states/sensor.kitchen_temperature"
        headers = {"Authorization": "Bearer TOKEN", "content-type": "application/json"}
        data = {"state": "25", "attributes": {"unit_of_measurement": "°C"}}

        response = post(url, headers=headers, json=data)

        :param entity_id: The entity_id to post the state object for.
        :param state: The state object to post.
        :return: The response object.
        """
        url = self._format_entity_url(entity_id)
        if not state.get("state"):
            raise ValueError("State object must contain a state key.")
        response: Response = post(url, headers=self.headers, json=state)
        if not response.ok:
            raise ConnectionError(
                f"Error while posting entity {entity_id}: {response.reason}"
            )
        if response.status_code == 201:
            _LOGGER.debug("Successfully created entity %s", entity_id)
        elif response.status_code == 200:
            _LOGGER.debug("Successfully updated entity %s", entity_id)
        return response

    def _format_entity_url(self, entity_id: str) -> str:
        """Format the url to the Home Assistant API for the specified entity_id."""
        if not len(entity_id.split(".")) == 2:
            raise ValueError(f"Invalid entity_id: {entity_id}")
        return urljoin(self.url, f"states/{entity_id}")


@dataclass
class HassEntity:
    """Home Assistant API backed entity."""

    entity_id: str
    api: HassAPI
    dtype: str
    unit_of_measurement: str = field(default="")
    precision: int = field(default=1)
    icon: str = field(default="")
    idempotent: bool = field(default=True)
    _state: Any = field(init=False)

    def __post_init__(self):
        self._state = None

    @property
    def state(self) -> Any:
        """Return the state of the entity."""
        return self._state

    @state.setter
    def state(self, value: Any):
        """Set the state of the entity."""
        self._state = value

    def update(self, state: Any) -> None:
        """Update the entity state.

        :param state: The new state of the entity.
        """
        # coerce the state to the correct type
        try:
            state = self.dtype(state)
            if self.dtype == float:
                state = round(state, self.precision)
        except ValueError:
            _LOGGER.error("Error converting %s to %s", state, self.dtype)
            return
        if self.idempotent and self.state == state:
            return
        self.state = state

        # compile state dictionary
        state_dict = {
            "state": self.state,
            "attributes": {
                "unit_of_measurement": self.unit_of_measurement,
                "icon": self.icon,
            },
        }

        # post the state to the API
        try:
            self.api.post_entity_state(self.entity_id, state_dict)
        except ConnectionError as err:
            _LOGGER.error("Error while posting entity %s: %s", self.entity_id, err)
            return
        except ValueError as err:
            _LOGGER.error("Error while posting entity %s: %s", self.entity_id, err)
            return
