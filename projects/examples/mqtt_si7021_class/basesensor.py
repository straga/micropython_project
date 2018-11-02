from mqtt_helpers import make_publish


class BaseSensor():
    """Common functions for all sensors"""
    def action_on_change(self, source, value):
        if value and self.publish_state_to_mqtt:
            global MESSAGES
            if value[0]:
                MESSAGES[CONFIG['topic'] + "/Sensor01_TEMP"] = str(value[0])
            if value[1]:
                MESSAGES[CONFIG['topic'] + "/Sensor01_HUM"] = str(value[1])
            loop.create_task(make_publish(event))

    def get_state(self):
        return self.measure()