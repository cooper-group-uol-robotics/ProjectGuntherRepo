"""Ejecting MS Sample Rack 1."""

import logging

import serial
import zmq

from synthesis_bots.utils.constants import DRY

logger = logging.getLogger(__name__)


def main(
    pub: "zmq.Socket",
    sub: "zmq.Socket",
):
    """Eject LCMS RACK1."""
    if DRY:
        print(__name__)
    else:
        logger.info("Starting ejecting RACK1.")
        # Open serial port to the LCMS
        ser = serial.Serial("COM4", 38400, timeout=20)
        ser.write(b"Extract(1)\r")
        print(ser.readline().decode("gbk").strip())
        print(ser.readline().decode("gbk").strip())
        result = (
            ser.read(8).decode("gbk").strip()
        )  # strip use to eliminate space
        if result in "Completed":
            logger.info("Rack ejected successfully.")
            pub.send_string("[LCMSAS] Extract Rack 1 Completed\n")
        else:
            logger.error("Rack ejection failed.")
            pub.send_string("[LCMSAS] Error! Extract Rack 1\n")
        ser.close()
