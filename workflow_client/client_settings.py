import os
import simplejson as json
import yaml

def load_settings_yaml():
    try: 
        blue_sky_settings_json = os.getenv('BLUE_SKY_SETTINGS')
    except:
        raise Exception('need to set BLUE_SKY_SETTINGS')

    class settings_attr_dict(dict):
        __getattr__ = dict.get

    with open(blue_sky_settings_json) as f:
        settings = settings_attr_dict(yaml.load(f))

    return settings


settings = load_settings_yaml()
