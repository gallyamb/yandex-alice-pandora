"""Device tracker for Pandora Car Alarm System component"""
__all__ = ("async_setup_entry", "PLATFORM_DOMAIN")

import base64
import logging
from typing import Any, Dict
from urllib.parse import quote

from homeassistant import config_entries
from homeassistant.components.device_tracker import (
    DOMAIN as PLATFORM_DOMAIN,
    SOURCE_TYPE_GPS,
)
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_VOLTAGE, CONF_USERNAME
from homeassistant.helpers.typing import HomeAssistantType

from . import BasePandoraCASEntity
from .api import PandoraOnlineAccount, PandoraOnlineDevice
from .const import *

_LOGGER = logging.getLogger(__name__)

DEFAULT_ADD_DEVICE_TRACKER: Final = True


TRACKER_IMAGE_SOURCE: Final = """
<?xml version="1.0" ?>
<svg height="512" id="svg3007" version="1.1" width="512"
    xmlns="http://www.w3.org/2000/svg"
    xmlns:cc="http://creativecommons.org/ns#"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    xmlns:svg="http://www.w3.org/2000/svg">
    <path d="m 217.13642,146.13435 c -0.0357,6e-4 -0.14981,0.0181 -0.24,0.02 -0.87778,0.0194 -3.99768,0.0945 -5.7,0.48 -1.90342,0.43104 -3.80556,1.01751 -5.48,2.02 -2.50472,1.49965 -4.61679,3.64138 -6.56,5.82 -1.62169,1.81818 -2.86241,3.94371 -4.2,5.98 -0.53772,0.81863 -1.23176,1.58394 -1.52,2.52 -0.0398,0.12911 -0.093,0.24477 -0.12,0.38 -31.25675,0.0882 -62.51305,0.31019 -93.759999,1.02 -18.762206,0.62707 -37.167472,10.05239 -47.439992,25.98 -4.401784,5.13425 -7.214072,11.19834 -8.48,17.76 -7.317976,19.75288 -4.191064,41.28355 -4.86,61.9 -0.621408,16.44047 2.831368,32.97476 10.28,47.6 8.660096,13.64969 21.606544,25.82672 38.159996,28.3 23.190605,4.82131 47.075915,2.08365 70.579995,2.88 11.85404,-0.0263 23.70564,-0.0182 35.56,-0.02 0.0203,0.0847 0.0548,0.15807 0.08,0.24 0.28824,0.93606 0.98228,1.70139 1.52,2.52 1.33759,2.03628 2.57831,4.16185 4.2,5.98 1.94321,2.17863 4.05528,4.32039 6.56,5.82 1.67444,1.00252 3.57658,1.58899 5.48,2.02 1.70232,0.38547 4.82222,0.46069 5.7,0.48 0.39521,0.0811 0.81989,0.0108 1.1,-0.2 0.28011,-0.21079 0.36846,-0.41857 0.44,-0.9 0.0715,-0.48141 -6e-4,-0.68937 -0.32,-1.9 -0.31915,-1.21063 -1.08197,-3.31953 -1.9,-5.24 -0.81803,-1.92046 -2.17583,-4.55649 -3.08,-6.22 -0.57813,-1.06366 -1.04799,-1.86772 -1.5,-2.6 15.42148,0.007 30.83838,0.007 46.26,0.02 0.0542,0.0712 0.11147,0.14771 0.18,0.22 0.35576,0.37523 0.87286,0.87216 1.86,1.22 0.98715,0.34784 1.03685,0.25022 4.04,0.4 3.00315,0.14979 10.61173,0.0969 12.84002,-0.04 2.22829,-0.13693 2.62509,-0.17186 3.72,-0.6 0.88435,-0.3458 1.54445,-0.51239 1.68,-1.18 23.49574,0.006 47.00493,-0.021 70.50003,-0.12 0.86375,0.29284 1.05882,0.21734 3.92,0.36 3.00288,0.14979 10.63168,0.0969 12.85997,-0.04 1.8375,-0.11291 2.43552,-0.16667 3.2,-0.42 19.41229,-0.12141 38.82912,-0.30509 58.24,-0.58 13.57414,0.032 27.06349,-8.42931 31.62003,-21.48 11.63763,-28.70999 11.42835,-60.54084 10.24,-91.04 -1.52,-19.91366 -4.08928,-40.86446 -14.88,-58.06 -9.66841,-13.69542 -28.30093,-14.09957 -43.48006,-14.04 -14.29447,-0.14953 -28.58432,-0.20843 -42.88,-0.24 -0.4857,-0.0644 -1.07834,-0.11966 -2.05997,-0.18 -2.22829,-0.13683 -9.85709,-0.18976 -12.85997,-0.04 -1.97113,0.0983 -2.63309,0.0978 -3.16006,0.18 -18.30637,-0.005 -36.61344,0.0394 -54.91994,0.04 -5.43936,0.0294 -10.88083,0.0422 -16.32006,0.06 -0.11418,-0.70563 -0.79635,-0.86663 -1.69997,-1.22 -1.09491,-0.42816 -1.49171,-0.4631 -3.72,-0.6 -2.22829,-0.13689 -9.83687,-0.18982 -12.84002,-0.04 -3.00315,0.14976 -3.05285,0.0522 -4.04,0.4 -0.98714,0.34784 -1.50424,0.84477 -1.86,1.22 -0.0889,0.0938 -0.17716,0.18699 -0.24,0.28 -15.42082,0.0197 -30.8389,0.0388 -46.26,0.06 0.47103,-0.75771 0.95512,-1.58712 1.56,-2.7 0.90417,-1.66355 2.26197,-4.29949 3.08,-6.22 0.81803,-1.92045 1.58085,-4.02937 1.9,-5.24 0.3194,-1.21069 0.39154,-1.41853 0.32,-1.9 -0.0715,-0.48141 -0.15989,-0.68925 -0.44,-0.9 -0.19148,-0.14425 -0.45165,-0.21013 -0.72,-0.22 -0.0456,-0.002 -0.0939,-0.002 -0.14,0 z m 52.58,17.08 c 0.56925,-0.006 1.21616,-0.006 1.84,0.02 -0.88726,0.002 -1.77272,-0.002 -2.66,0 0.28238,-0.011 0.57178,-0.0172 0.82,-0.02 z m 161.62002,7.32 c 3.98362,-0.10006 8.47507,0.49707 10.90003,1.74 5.93658,3.04302 9.49709,7.73067 10.88,14.34 0.45127,2.15734 1.52666,5.29191 2.37997,6.98 2.53837,5.02162 4.8743,12.28169 4.66003,14.46 l -0.20006,2.02 -1.97997,-1.86 c -1.08813,-1.02017 -2.95002,-3.95264 -4.12,-6.52 -6.77248,-14.86119 -15.81574,-23.51737 -29.6,-28.36 -1.19942,-0.42138 -1.19046,-0.46785 -0.0602,-1.3 1.2583,-0.92616 4.04166,-1.42217 7.14003,-1.5 z m -214.34002,1.26 c 1.28877,-0.008 2.76232,-0.003 4.4,0 10.91785,0.021 29.10184,0.26157 48.16,0.66 l 13.59999,0.28 5.30003,8.32 c 2.91123,4.56694 5.37677,8.74014 5.48,9.28 0.18515,0.96863 0.13594,0.96669 -4.10003,0.9 -2.3609,-0.0372 -8.51539,-0.213 -13.65997,-0.4 -14.53322,-0.52824 -36.94353,-2.85729 -51.10002,-5.3 l -5.66,-0.96 -1.82,-2.84 c -1.00208,-1.55534 -2.8663,-4.27453 -4.14,-6.06 -1.27368,-1.78547 -2.38732,-3.43261 -2.48,-3.66 -0.0463,-0.11365 2.15371,-0.19541 6.02,-0.22 z m -127.579995,0.46 c 1.03944,5e-5 2.21927,-0.006 3.559996,0 14.445959,0.0595 17.025159,1.16889 11.499999,4.9 -3.1921,2.15562 -23.743005,14.63843 -32.059991,19.48 -7.071624,4.11661 -9.857224,6.48779 -13.02,11.08 -1.273056,1.84842 -3.206832,3.77177 -4.32,4.3 -2.067376,0.98104 -5.291528,1.26847 -6.02,0.54 -0.2256,-0.2256 -0.42,-2.03475 -0.42,-4.02 0,-3.85553 1.171272,-6.73686 5.4,-13.4 3.47964,-5.48282 10.249448,-13.16521 14.26,-16.18 2.051664,-1.54227 6.009864,-3.7001 8.8,-4.78 4.407076,-1.70571 5.043876,-1.92031 12.319996,-1.92 z m 217.499985,0.82 c 1.64902,-0.004 4.24409,0.059 8.26003,0.16 33.70726,0.84835 55.6313,1.59333 55.89997,1.88 0.45107,0.48013 1.70003,8.21307 1.70003,10.54 0,3.62553 0.2832,3.52308 -12.21997,4.18 -8.3664,0.43955 -40.07334,1.42795 -47.62003,1.48 -0.73446,0.005 -1.54112,-1.45207 -4.66003,-8.4 -2.07354,-4.61928 -3.91565,-8.75175 -4.08,-9.18 -0.17735,-0.46263 -0.0282,-0.65358 2.72,-0.66 z m 84.34003,4.84 c 0.72762,-0.0236 1.62912,0.0285 2.77997,0.12 4.51046,0.35861 15.21165,1.87641 15.80006,2.24 1.26336,0.78093 -5.23923,3.08808 -13.2,4.7 -5.92525,1.19971 -6.61395,1.27001 -8.08,0.68 -1.36211,-0.54802 -1.63193,-2.19514 -0.78003,-4.76 0.7241,-2.18021 1.29715,-2.90916 3.48,-2.98 z m -238.72002,3.74 c 1.92495,0 55.0127,11.67285 64.22,14.12 6.20751,1.64986 17.61444,5.50446 25.34,8.56 17.578,6.95228 26.56977,9.32 35.44002,9.32 6.75187,0 7.14182,0.17929 12.68,6.1 l 5.69997,6.1 0,30.24 0,30.26 -5.56,5.94 -5.53997,5.92 -10.76,0.64 c -8.48659,0.49582 -13.21812,1.58867 -22.44002,5.18 -22.9803,8.94935 -37.94438,13.3134 -65.84,19.26 -15.56638,3.31834 -29.53522,6.31725 -31.04,6.66 -2.20387,0.50201 -3.18789,-0.27063 -5.08,-4 -2.90944,-5.73456 -9.30603,-25.69652 -11.14,-34.78 -4.04471,-20.03301 -3.72723,-55.65604 0.64,-73.22 4.07268,-16.37935 11.41631,-36.3 13.38,-36.3 z m 285.20002,6.3 c 3.39469,-0.16631 4.42317,2.7662 8.12,9.7 10.05459,18.8585 13.09901,35.10049 12.16,65 -0.7367,23.45759 -2.7319,32.47286 -10.86003,49 -7.08256,14.40155 -7.26835,14.50003 -17.71994,9.52 -4.73773,-2.25733 -11.80845,-5.30076 -15.70003,-6.76 -3.89158,-1.45924 -7.08,-2.87539 -7.08,-3.14 0,-0.26461 1.92986,-4.29313 4.28,-8.96 7.37645,-14.64765 9.7945,-26.29157 9.72,-46.82 -0.0746,-20.54911 -2.2448,-30.75562 -9.68,-45.52 -2.45971,-4.88434 -4.29261,-9.02499 -4.08,-9.2 0.21267,-0.17501 7.53171,-3.42994 16.25997,-7.24 7.88019,-3.43972 11.93971,-5.45064 14.58003,-5.58 z m -387.220011,110.9 c 0.488216,-0.0427 1.092504,0.0414 1.84,0.22 3.658824,0.87423 4.193248,1.29611 7.28,5.54 3.662152,5.035 5.749016,6.70139 14.84,11.96 13.471746,7.79265 31.589331,19.14478 32.239991,20.2 1.39475,2.26194 -0.26505,2.64016 -12.719999,2.78 -10.283886,0.11546 -12.234546,-0.0221 -15.039996,-1.04 -9.37962,-3.40338 -16.845044,-9.75316 -23.879996,-20.32 -5.177544,-7.77691 -6.403456,-10.62042 -6.42,-14.86 -0.01216,-3.10701 0.395344,-4.35201 1.86,-4.48 z m 409.439981,3.22 0.18003,1.84 c 0.21709,2.13231 -2.36992,10.22075 -4.56,14.22 -0.81773,1.49331 -1.90208,4.67187 -2.4,7.06 -2.11981,10.16655 -9.97318,16.47352 -20.26003,16.3 -2.05351,-0.0346 -4.57319,-0.25391 -5.6,-0.5 -1.02669,-0.24609 -2.40218,-0.75186 -3.05997,-1.12 -1.11949,-0.62647 -1.07507,-0.7076 0.64,-1.4 7.98688,-3.22453 12.3808,-5.8991 16.6,-10.06 5.0361,-4.96646 8.20346,-9.57455 12.29997,-17.94 1.55609,-3.17773 3.56461,-6.37662 4.48,-7.1 l 1.68,-1.3 z m -147.92,18.66 8.72,0.1 c 10.58528,0.11951 31.39923,0.84934 42.66003,1.48 6.70989,0.3758 8.35859,0.59064 8.8,1.16 0.75008,0.96743 0.67104,4.78806 -0.21997,9.44 l -0.76006,3.9 -1.95994,0.3 c -1.89913,0.28723 -24.57369,0.96055 -51.92,1.54 -9.47449,0.20075 -13.39897,0.14826 -13.28,-0.18 0.0927,-0.25608 1.91987,-4.35166 4.05997,-9.1 l 3.89997,-8.64 z m -25.76,0.18 c 4.69472,-0.008 7.74003,0.17931 7.74003,0.62 0,0.57002 -9.58381,16.05708 -10.62003,17.16 -0.51059,0.54346 -11.65154,0.83563 -60.17999,1.56 l -12.7,0.2 1.78,-2.46 c 0.9853,-1.35083 2.97553,-4.28071 4.42,-6.5 1.60182,-2.46103 2.9892,-4.11686 3.54,-4.24 4.92828,-1.1018 23.75501,-3.61132 35.48,-4.74 10.33749,-0.99511 22.71554,-1.58634 30.53999,-1.6 z m 104.58003,5.28 c 1.80902,0.0252 4.37696,0.46624 7.88,1.26 8.77434,1.98822 13.20595,3.94811 10.28,4.56 -2.82042,0.58983 -11.11066,1.60575 -15.22003,1.86 l -4.41997,0.26 -0.88,-1.44 c -0.48224,-0.79289 -1.00243,-2.20768 -1.16,-3.14 -0.39418,-2.3334 0.50496,-3.40202 3.52,-3.36 z" id="path4400-3-2" style="color:#000000;fill:${COLOR};fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.1;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate" transform="rotate(${ROTATION} 256 256)"/>
</svg>
"""
TRACKER_IMAGE_BASE_ROTATION: Final = 90


async def async_setup_entry(
    hass: HomeAssistantType, config_entry: ConfigEntry, async_add_devices
):
    account_cfg = config_entry.data
    username = account_cfg[CONF_USERNAME]

    if config_entry.source == config_entries.SOURCE_IMPORT:
        account_cfg = hass.data[DATA_CONFIG][username]

    account_object: PandoraOnlineAccount = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for device in account_object.devices:
        # Use default settings for device directive
        device_directive = DEFAULT_ADD_DEVICE_TRACKER

        # Skip platform directives for definitions
        platform_directive = account_cfg.get(PLATFORM_DOMAIN)
        if isinstance(platform_directive, bool):
            device_directive = platform_directive
        elif platform_directive is not None:
            device_directive = platform_directive.get(str(device.device_id))
            if device_directive is None:
                device_directive = platform_directive.get(ATTR_DEFAULT)

        # Barrier disabled device trackers
        if device_directive is False or (
            device_directive is None and not DEFAULT_ADD_DEVICE_TRACKER
        ):
            _LOGGER.debug(
                'Skipping device "%s" during platform "%s" setup'
                % (device.device_id, PLATFORM_DOMAIN)
            )
            continue

        # Add device tracker
        _LOGGER.debug(
            'Adding "%s" object to device "%s"' % (PLATFORM_DOMAIN, device.device_id)
        )
        new_devices.append(PandoraCASTracker(device))

    if new_devices:
        async_add_devices(new_devices, True)
        _LOGGER.debug('Added device trackers for account "%s"' % (username,))
    else:
        _LOGGER.debug('Did not add any device trackers for account "%s"' % (username,))

    return True


class PandoraCASTracker(BasePandoraCASEntity, TrackerEntity):
    """Pandora Car Alarm System location tracker."""

    def __init__(self, device: PandoraOnlineDevice):
        super().__init__(device, "location_tracker")

        self._device_state = device.state

        self.entity_id = "%s.%s_%d" % (
            PLATFORM_DOMAIN,
            ".pandora_",
            self._device.device_id,
        )

    async def async_update(self):
        """Simplistic update of the device tracker."""
        device = self._device

        if not device.is_online:
            self._available = False
            return

        self._device_state = device.state
        self._available = True

    @property
    def name(self) -> str:
        """Return device name for this tracker entity."""
        return self._device.name

    @property
    def icon(self) -> str:
        """Use vehicle icon by default."""
        return "mdi:car"

    @property
    def latitude(self) -> float:
        """Return latitude value of the device."""
        device_state = self._device_state
        if device_state is None:
            return 0.0
        return device_state.latitude

    @property
    def longitude(self) -> float:
        """Return longitude value of the device."""
        device_state = self._device_state
        if device_state is None:
            return 0.0
        return device_state.longitude

    @property
    def entity_picture(self) -> str:
        color = self._device.color or "#000000"

        device_state = self._device_state
        base_rotation = (device_state.rotation if device_state else None) or 0
        rotation = str(base_rotation + TRACKER_IMAGE_BASE_ROTATION)

        img_str = TRACKER_IMAGE_SOURCE.replace("${COLOR}", color)
        img_str = img_str.replace("${ROTATION}", rotation)
        img_str = img_str.replace("\n", "").replace("\r", "")
        img_str = (
            "data:image/svg+xml;base64," + base64.b64encode(img_str.encode()).decode()
        )

        return img_str

    @property
    def source_type(self):
        """Default to GPS source only."""
        return SOURCE_TYPE_GPS

    @property
    def device_state_attributes(self) -> Dict[str, Any]:
        """Add some additional device attributes."""
        attributes = {}
        device_state = self._device_state

        attributes.update(super().device_state_attributes)
        if device_state is None:
            attributes.update(
                dict.fromkeys(
                    (
                        ATTR_VOLTAGE,
                        ATTR_GSM_LEVEL,
                        ATTR_DIRECTION,
                        ATTR_CARDINAL,
                        ATTR_KEY_NUMBER,
                        ATTR_TAG_NUMBER,
                    )
                )
            )
        else:
            attributes[ATTR_VOLTAGE] = device_state.voltage
            attributes[ATTR_GSM_LEVEL] = device_state.gsm_level
            attributes[ATTR_DIRECTION] = device_state.rotation
            attributes[ATTR_CARDINAL] = device_state.direction
            attributes[ATTR_KEY_NUMBER] = device_state.key_number
            attributes[ATTR_TAG_NUMBER] = device_state.tag_number

        return attributes
