import subprocess
import logging
from ppadb.client import Client as AdbClient
import re
import json
logger = logging.getLogger(__name__)
logging.basicConfig(filename="connect_to_phone.log", level=logging.INFO)

adb_client = AdbClient()

saved_devices_config = "saved_devices.json"


def start_adb():
    subprocess.run(["adb", "devices"])


def save_device(serial, ip, model):
    """
    Adds a new device to the JSON configuration file if the serial doesn't already exist.

    :param file_path: Path to the JSON configuration file.
    :param serial: Serial number of the device.
    :param ip: IP address of the device.
    :param model: Model of the device.
    """
    try:
        with open(saved_devices_config, 'r') as file:
            saved_devices = json.load(file)

        if "devices" not in saved_devices or not isinstance(saved_devices["devices"], list):
            saved_devices["devices"] = []

        for device in saved_devices["devices"]:
            if device.get("serial") == serial:
                logger.info(f"Device with serial {serial} already exists.")
                return

        saved_devices["devices"].append({"serial": serial, "ip": ip, "model": model})
        with open(saved_devices_config, 'w') as file:
            json.dump(saved_devices_config, file, indent=2)
        logger.info(f"Device with serial {serial} added successfully.")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except FileNotFoundError:
        print(f"File not found: {saved_devices_config}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def get_device_name(dev):
    try:
        device_name = (dev.shell("getprop ro.product.manufacturer").strip() +
                       " " + dev.shell("getprop ro.product.model").strip())
        # print(f"Manufacturer: {manufacturer}, Model: {model}")

    except RuntimeError as err:
        logger.warning(str(err))
        device_name = "Unknown Model"
    return device_name


def get_device_ip(dev):
    try:
        dev_ip_full = dev.shell("ip addr show wlan0")
        dev_ip = re.search(r"inet (\d{1,3}(?:\.\d{1,3}){3})", dev_ip_full).group(1)
        return dev_ip
    except RuntimeError as err:
        return ""


def get_devices_list_of_dict():
    devlist = adb_client.devices()
    devices = []
    for i in range(len(devlist)):
        d_dict = {}
        d = devlist[i]
        d_dict["name"] = get_device_name(d)
        d_dict["serial"] = d.serial
        d_dict["ip"] = get_device_ip(d)
        devices.append(d_dict)
    return devices


def get_device_dict_with_serial(device_dict_list: list[dict], serial: str):
    for dev in device_dict_list:
        if dev["serial"] == serial:
            return dev
