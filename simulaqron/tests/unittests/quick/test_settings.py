import unittest
import json
import random

from simulaqron.settings import simulaqron_settings


#####################
# TODO Add more tests
#####################

class TestSettings(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        simulaqron_settings.default_settings()

    def test_default_settings(self):
        simulaqron_settings.default_settings()
        for key, value in simulaqron_settings._default_config.items():
            self.assertEqual(getattr(simulaqron_settings, key), value)

    def test_set_settings(self):
        new_settings = {}
        for key in simulaqron_settings._default_config:
            value = random.randint(0, 100)
            new_settings[key] = value
            setattr(simulaqron_settings, key, value)

        with open(simulaqron_settings._internal_settings_file, 'r') as f:
            file_settings = json.load(f)

        for key, value in new_settings.items():
            self.assertEqual(getattr(simulaqron_settings, key), value)
            self.assertEqual(value, file_settings[key])

        self.test_default_settings()


if __name__ == '__main__':
    unittest.main()
