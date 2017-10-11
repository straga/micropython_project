import ssd1306
from machine import I2C, Pin

# OLED 128x64

i2c = I2C(sda=Pin(22), scl=Pin(21))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
display.fill(0)

display.text('Hello',10,10)
display.show()
