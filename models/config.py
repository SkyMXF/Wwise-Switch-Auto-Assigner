import os
import json

from log import LOGGER


class UserConfig(object):

    def __init__(self):
        self.object_name_replacement: dict[str, str] = {
            "example_name_replacement_switch_auto_assigner": "example_new_name"
        }
        self.special_switch_group_cut_words: list[str] = [
            "write_switch_group_name_here",
            "and_switch_container_child_name_will_be_cut",
            "by_their_parents_name",
        ]

    def load(self, file_path: str, create_if_not_exists: bool = True):
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)
            for data_key, data_value in data.items():
                if hasattr(self, data_key):
                    setattr(self, data_key, data_value)
            LOGGER.debug(f"User config loaded from {file_path}.")
        elif create_if_not_exists:
            LOGGER.debug(f"User config not found. "
                         f"Creating default user config at {file_path}.")
            self.save(file_path)
        else:
            LOGGER.error(f"User config not found at {file_path}.")

    def save(self, file_path: str):
        dir_path = os.path.dirname(file_path)
        if len(dir_path) > 0:
            os.makedirs(dir_path, exist_ok=True)

        data = {}
        for key, value in self.__dict__.items():
            if not key.startswith("__"):
                data[key] = value

        with open(file_path, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        LOGGER.debug(f"User config saved to {file_path}.")
