import subprocess
import usb.core
import logging
from ppadb.client import Client as AdbClient
logger = logging.getLogger(__name__)
logging.basicConfig(filename="connect_to_phone.log", level=logging.INFO)


def enumerate_usb_devices():
    return [d for d in usb.core.find(find_all=True)]


def enumerate_android_devices():
    client = AdbClient()
    return client.devices()


def check_for_usb_device_exist(vid=0x18D1, pid=0x4EE7):
    """
    Check if the USB device with the specified vid and pid is connected
    :param vid: The VID of the device
    :param pid: The PID of the device
    :return: True if connected, False if not.
    """
    devices = enumerate_usb_devices()
    for d in devices:
        if d.idVendor == vid and d.idProduct == pid:
            return True
    return False


class ScreenConnector:
    """
    An instance of a screen connector that casts the screen of ONE android device to your PC

    Attributes:
        serial: str. The serial number of the phone to be connected
        address: str. The IP address of the phone to be connected.
    """
    serial: str
    address: str

    def __init__(self, serial, ip, adb_client=None):
        self.serial = serial
        self.address = ip
        if not adb_client:
            self.adbClient = AdbClient()

    def connect_tcpip(self):
        # default should be 192.168.2.10
        try:
            subprocess.run(["scrcpy", f"--tcpip={self.address}"], check=True)

        except subprocess.CalledProcessError as called_proc_err:
            print("TCP/IP Connection Failed. Please connect the phone via USB.")
            return

        # # This code could be useful in the future if we need parallel processing or need to access the stdout. Right now it makes things too complicated.
        # # bufsize=1 ensures the outputs are printed in real time.
        # with subprocess.Popen(["scrcpy", f"--tcpip={address}"], stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as p:
        #     for stdout_line in p.stdout:
        #         print(stdout_line, end='')

        # if p.returncode:
        #     raise subprocess.CalledProcessError(p.returncode, p.args)

    def setup_tcpip(self) -> bool:
        if not (self._setup_tcpip_directconnect()):
            if not (self._setup_tcpip_connectwithserial()):
                if not (self._setup_tcpip_authroizethenconnect()):
                    err = "TCPIP connection failed. Try debug your code."
                    logger.critical(err)

        return False

    def _setup_tcpip_directconnect(self) -> bool:
        try:
            subprocess.run(["adb", "tcpip", "5555"],  capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError as err:
            logger.error(str(err.stderr))
        return False

    def _setup_tcpip_connectwithserial(self) -> bool:
        try:
            subprocess.run(["adb", "-s", self.serial, "tcpip", "5555"], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError as err:
            logger.error(str(err.stderr))
        return False

    def _setup_tcpip_authroizethenconnect(self) -> bool:
        try:
            subprocess.run(["adb", "kill-server"], capture_output=True, check=True)
            subprocess.run(["adb", "-s", self.serial, "tcpip", "5555"], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError as err:
            logger.critical(str(err.stderr))
            if err.stderr == ErrorStrings.UNAUTHORIZED:
                input("Device Unauthorized. See if there is a confirmation dialog on your phone. "
                      "If so, confirm the dialog then press enter to continue")
            return self._setup_tcpip_connectwithserial()


class ErrorStrings:
    UNAUTHORIZED = (b"* daemon not running; starting now at tcp:5037"
                    b"\r\n* daemon started successfully\r\nerror: device unauthorized."
                    b"\r\nThis adb server's $ADB_VENDOR_KEYS is not set\r\nTry 'adb kill-server' "
                    b"if that seems wrong.\r\nOtherwise check for a confirmation dialog on your device.\r\n")
