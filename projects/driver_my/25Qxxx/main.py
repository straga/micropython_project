import machine
import uos
from flash import FlashClass

# pinCS = machine.Pin(machine.Pin.board.PB3, machine.Pin.OUT)

flash_cs = machine.Pin.board.PB3
flash_spi_bus = 3

flash = FlashClass(flash_spi_bus, flash_cs)
uos.mount(flash, '/fs')
#uos.umount('/fs')
# self.flash = FlashClass(intside)
# self.umountflash()  # In case mounted by prior tests.
# self.mountflash()

# import pyb, flash, os
# f = flash.FlashClass(0) # If on right hand side pass 1
# f.low_level_format()
# pyb.mount(f, f.mountpoint, mkfs=True)
# flash.cp('/sd/LiberationSerif-Regular45x44','/fc/')
# os.listdir('/fc')
# pyb.mount(None, '/fc')