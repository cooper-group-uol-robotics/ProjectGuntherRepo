"""Workflow Entity class."""

import logging
import sys
from enum import StrEnum
from importlib import import_module

import zmq

from synthesis_bots.utils.constants import SETTINGS

logger = logging.getLogger(__name__)


class Instrument(StrEnum):
    """Implemented instruments."""

    LCMS = "LCMS"
    NMR = "NMR"


class WorkflowEntity:
    """Autonomous chemistry worklow entity."""

    def __init__(
        self,
        instrument_address: str,
        host_address: str,
        instrument: Instrument,
    ) -> None:
        """
        Initialise WorkflowEntity.

        Parameters
        ----------
        instrument_address
            TCP address of the instrument.
        host_address
            TCP address of the host.
        instrument
            Instrument name.

        """
        logger.info(f"Initialising network interface for {instrument.value}.")
        self.instrument = instrument
        self.workflows = SETTINGS["workflows"][self.instrument.name]

        self.instrument_ip = instrument_address
        self.host_ip = host_address

        self.context = zmq.Context()
        self.sub = self.context.socket(zmq.SUB)
        self.pub = self.context.socket(zmq.PUB)
        self.ser = None

    def await_command(self):
        """Await workflow commands."""
        while True:
            try:
                topic, cmd = self.sub.recv_multipart()
                logger.info(f"Received topic: {topic.decode()}")
                logger.info(f"Received command: {cmd.decode()}")
                self.execute_command(cmd)
            except KeyboardInterrupt:
                self.close()
            except Exception as e:
                logger.error(f"Error: {e}.")

    def connect(self):
        """Connect WorkflowEntity to the Host."""
        try:
            self.sub.connect(self.host_ip)
            self.sub.setsockopt_string(zmq.SUBSCRIBE, self.instrument.value)
            self.pub.bind(self.instrument_ip)
            logger.info(
                f"Connected the {self.instrument.value} "
                f"({self.instrument_ip}) to the host at {self.host_ip}."
            )

        except Exception:
            logger.error("Connection failed.")
            self.close()
            sys.exit(1)

    def close(self):
        """Close network connection to the Host."""
        if self.ser:
            self.ser.close()

        self.sub.close()
        self.pub.close()
        self.context.term()
        sys.exit(1)

    def execute_command(
        self,
        cmd: bytes,
    ):
        """
        Execute a workflow command.

        Parameters
        ----------
        cmd
            Workflow command.

        """
        if cmd.decode() not in self.workflows.keys():
            logger.error("Error! Please re-run this file.")
            self.pub.send_string(
                f"[{self.instrument.value}] Error! Unknown command received.\n"
            )
            self.close()

        else:
            workflow_module = self.workflows[cmd.decode()]
            logger.info(f"Executing a workflow from: {workflow_module}.")
            workflow = import_module(workflow_module)
            workflow.main(pub=self.pub, sub=self.sub)
            logger.info("Workflow execution finished.")
