# coding: utf-8
import gc
gc.collect()

import sx127x
gc.collect()

import test
# import test_dual_channels as test
gc.collect()
test.main()


import oled

oled.display.fill(0)
oled.display.text('Hello')
oled.display.show()