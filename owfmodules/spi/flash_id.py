# -*- coding: utf-8 -*-

# Octowire Framework
# Copyright (c) ImmunIT - Jordan Ovrè / Paul Duncan
# License: Apache 2.0
# Paul Duncan / Eresse <pduncan@immunit.ch>
# Jordan Ovrè / Ghecko <jovre@immunit.ch>

import codecs

from octowire.spi import SPI
from octowire.gpio import GPIO
from octowire_framework.module.AModule import AModule


class FlashID(AModule):
    def __init__(self, owf_config):
        super(FlashID, self).__init__(owf_config)
        self.meta.update({
            'name': 'SPI flash ID',
            'version': '1.0.1',
            'description': 'Obtain identification information of SPI flash devices (RDID)',
            'author': 'Jordan Ovrè / Ghecko <jovre@immunit.ch>, Paul Duncan / Eresse <pduncan@immunit.ch>'
        })
        self.options = {
            "spi_bus": {"Value": "", "Required": True, "Type": "int",
                        "Description": "SPI bus (0=SPI0 or 1=SPI1)", "Default": 0},
            "cs_pin": {"Value": "", "Required": True, "Type": "int",
                       "Description": "GPIO used as chip select (CS)", "Default": 0},
            "spi_baudrate": {"Value": "", "Required": True, "Type": "int",
                             "Description": "SPI frequency (1000000 = 1MHz) maximum = 50MHz", "Default": 1000000},
            "spi_polarity": {"Value": "", "Required": True, "Type": "int",
                             "Description": "SPI polarity (1=high or 0=low)", "Default": 0},
            "spi_phase": {"Value": "", "Required": True, "Type": "string",
                          "Description": "SPI phase (1=high or 0=low)", "Default": 0}
        }

    def flash_id(self):
        bus_id = self.options["spi_bus"]["Value"]
        cs_pin = self.options["cs_pin"]["Value"]
        spi_baudrate = self.options["spi_baudrate"]["Value"]
        spi_cpol = self.options["spi_polarity"]["Value"]
        spi_cpha = self.options["spi_phase"]["Value"]
        spi_interface = SPI(serial_instance=self.owf_serial, bus_id=bus_id)
        cs = GPIO(serial_instance=self.owf_serial, gpio_pin=cs_pin)
        cs.direction = GPIO.OUTPUT
        cs.status = 1
        spi_interface.configure(baudrate=spi_baudrate, clock_polarity=spi_cpol, clock_phase=spi_cpha)
        self.logger.handle("Sending RDID command...", self.logger.INFO)
        rdid_cmd = b'\x9f'
        # Enable chip select
        cs.status = 0
        spi_interface.transmit(rdid_cmd)
        # RDID command returns 3 bytes
        resp = spi_interface.receive(3)
        cs.status = 1
        if not resp:
            self.logger.handle("Unable to get a response from the SPI flash", self.logger.ERROR)
            return None
        flash_id = codecs.encode(resp, 'hex').decode().upper()
        manufacturer = flash_id[0:2]
        mem_type = flash_id[2:4]
        dev_id = flash_id[4:6]
        self.logger.handle(f"SPI flash ID:\n   - Manufacturer: {manufacturer}\n   - Memory type: {mem_type}\n"
                           f"   - Device ID: {dev_id}", self.logger.RESULT)
        return flash_id

    def run(self, return_value=False):
        """
        Main function.
        Print/return the ID of an SPI flash.
        :return: Nothing or bytes, depending on the 'return_value' parameter.
        """
        # Detect and connect to the Octowire hardware. Set the self.owf_serial variable if found.
        self.connect()
        if not self.owf_serial:
            return None
        try:
            flash_id = self.flash_id()
            if return_value:
                return flash_id
            return None
        except (Exception, ValueError) as err:
            self.logger.handle(err, self.logger.ERROR)
