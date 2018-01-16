
def receive(lora, oled):
    print("LoRa Receiver")


    ping = ""
    message_payload = ""
    message_rssi = ""

    while True:

        if ping == "":
            ping = "o"
        else:
            ping = ""

        if lora.receivedPacket():            
            lora.blink_led()
            payload = lora.read_payload()


            try:
                message_payload  = payload.decode()
            except Exception as e:
                print(e)

            message_rssi = lora.packetRssi()

            print("*** Received message ***\n{}".format(message_payload))
            print("with RSSI: {}\n".format(message_rssi))

        oled.display.fill(0)
        oled.display.text('m:'+ message_payload, 0, 10)
        oled.display.text('rssi:' + str(message_rssi), 0, 20)
        oled.display.text('standy:' + ping, 0, 30)
        oled.display.show()



