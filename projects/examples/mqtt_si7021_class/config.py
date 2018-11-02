def init_config():
    try:
        f = open("/config.json", "r")
        return True
        f.close()
    except:
        return False


def load_config(CONFIG):
    import ujson as json
    try:
        with open("/config.json") as f:
            config = json.loads(f.read())
    except (OSError, ValueError):
        print("Couldn't load /config.json")
    else:
        CONFIG.update(config)
        print("Loaded config from /config.json")


def save_config(CONFIG):
    import ujson as json
    try:
        with open("/config.json", "w") as f:
            f.write(json.dumps(CONFIG))
            print("Saved config to /config.json")
    except OSError:
        print("Couldn't save /config.json")


def save_default_config():
    from machine import unique_id
    from os import uname
    import ubinascii
    mqtt_root_topic = "devices"
    board_uid = uname()[0] + "_" + ubinascii.hexlify(unique_id()).decode()
    CONFIG['client_id'] = board_uid
    CONFIG['topic'] = mqtt_root_topic + "/" + board_uid
    CONFIG['broker'] = '127.0.0.1'
    CONFIG['port'] = 1883
    CONFIG['debug'] = 'False'
    save_config(CONFIG)
    load_config(CONFIG)
