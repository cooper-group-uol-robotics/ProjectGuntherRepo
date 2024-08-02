"""Inserting MS Sample Rack 2."""

import logging

import serial
import zmq

from synthesis_bots.utils.constants import DRY

logger = logging.getLogger(__name__)


def main(
    pub: "zmq.Socket",
    sub: "zmq.Socket",
):
    """Insert LCMS RACK2."""
    if DRY:
        print(__name__)
    else:
        logger.info("Starting insertion of RACK2.")
        # Open serial port to the LCMS
        ser = serial.Serial("COM4", 38400, timeout=20)
        ser.write(b"Insert(0)\r")
        print(ser.readline().decode("gbk").strip())
        print(ser.readline().decode("gbk").strip())
        result = (
            ser.read(8).decode("gbk").strip()
        )  # strip use to eliminate space
        if result in "Completed":
            logger.info("Rack inserted successfully.")
            pub.send_string("[LCMSAS] Insert Rack 2 Completed\n")
        else:
            logger.error("Rack insertion failed.")
            pub.send_string("[LCMSAS] Error! Insert Rack 2\n")
        ser.close()
