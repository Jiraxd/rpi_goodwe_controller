from RPLCD.i2c import CharLCD
from typing import List
import asyncio

class LCDManager:

    def __init__(self, _cols, _rows):
        self.lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=_cols, rows=_rows, dotsize=8)

    async def write_init_message(self, _ip):
        await asyncio.sleep(1)
        self.lcd.clear()
        self.lcd.write_string("Connecting...")
        self.lcd.lf()
        self.lcd.write_string("Inverter IP:")
        self.lcd.write_string(_ip)
    
    def write_lines(self, text: List[str]):
        self.lcd.clear()
        for line in text:
            self.lcd.write_string(line)
            self.lcd.lf()