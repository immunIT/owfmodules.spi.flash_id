# -*- coding:utf-8 -*-

# Octowire SPI flash id module
# Copyright (c) Jordan Ovrè / Paul Duncan
# License: GPLv3
# Paul Duncan / Eresse <eresse@dooba.io>
# Jordan Ovrè / Ghecko <ghecko78@gmail.com


import codecs

from octowire.spi import SPI
from octowire.gpio import GPIO
from octowire_framework.module.AModule import AModule


class FlashID(AModule):
    def __init__(self, owf_config):
        super(FlashID, self).__init__(owf_config)
        self.meta.update({
            'name': 'SPI flash ID',
            'version': '1.0.0',
            'description': 'Module getting the ID of an SPI flash (RDID)',
            'author': 'Jordan Ovrè <ghecko78@gmail.com> / Paul Duncan <eresse@dooba.io>'
        })
        self.options = [
            {"Name": "spi_bus", "Value": "", "Required": True, "Type": "int",
             "Description": "The octowire SPI bus (0=SPI0 or 1=SPI1)", "Default": 0},
            {"Name": "cs_pin", "Value": "", "Required": True, "Type": "int",
             "Description": "The octowire GPIO used as chip select (CS)", "Default": 0},
            {"Name": "spi_baudrate", "Value": "", "Required": True, "Type": "int",
             "Description": "set SPI baudrate (1000000 = 1MHz) maximum = 50MHz", "Default": 1000000},
            {"Name": "spi_polarity", "Value": "", "Required": True, "Type": "int",
             "Description": "set SPI polarity (1=high or 0=low)", "Default": 0},
            {"Name": "spi_phase", "Value": "", "Required": True, "Type": "string",
             "Description": "set SPI phase (1=high or 0=low)", "Default": 0}
        ]

    def flash_id(self):
        bus_id = self.get_option_value("spi_bus")
        cs_pin = self.get_option_value("cs_pin")
        spi_baudrate = self.get_option_value("spi_baudrate")
        spi_cpol = self.get_option_value("spi_polarity")
        spi_cpha = self.get_option_value("spi_phase")
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
            self.logger.handle("Unable to get a response while reading from the SPI flash", self.logger.ERROR)
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
        :return: Nothing or bytes, depending of the 'return_value' parameter.
        """
        # Detect and connect to the octowire hardware. Set the self.owf_serial variable if found.
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
