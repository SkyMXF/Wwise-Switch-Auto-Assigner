from enum import Enum


class WwiseObjectType(Enum):

    Unknown = -1

    StateGroup = 7
    SwitchContainer = 10
    SwitchGroup = 19
    Switch = 20


class WwiseObject(object):

    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.type: WwiseObjectType = WwiseObjectType.Unknown
        self.path: str = ""

    @staticmethod
    def from_dict(data: dict) -> "WwiseObject":
        obj = WwiseObject()
        obj.id = data.get("id", "")
        obj.name = data.get("name", "")
        obj.path = data.get("path", "")

        object_type_str = data.get("type", "")
        for obj_type in WwiseObjectType:
            if obj_type.name == object_type_str:
                obj.type = obj_type
                break

        return obj

    def __str__(self):
        return f"{self.name} {self.id}"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id


class WwiseProjectInfo(object):

    def __init__(self):
        self.id: str = ""
        self.project_path: str = ""
        self.name: str = ""
        self.platforms: list[WwiseProjectPlatformInfo] = []
        self.languages: list[WwiseProjectLanguageInfo] = []
        self.directories: WwiseProjectDirectoriesInfo = WwiseProjectDirectoriesInfo()

    @staticmethod
    def from_dict(data: dict) -> "WwiseProjectInfo":
        obj = WwiseProjectInfo()
        obj.id = data.get("id", "")
        obj.project_path = data.get("projectPath", "")
        obj.name = data.get("name", "")
        obj.platforms = [
            WwiseProjectPlatformInfo.from_dict(platform_data)
            for platform_data in data.get("platforms", [])
        ]
        obj.languages = [
            WwiseProjectLanguageInfo.from_dict(language_data)
            for language_data in data.get("languages", [])
        ]
        obj.directories = WwiseProjectDirectoriesInfo.from_dict(data.get("directories", {}))
        return obj


class WwiseProjectPlatformInfo(object):

    def __init__(self):
        self.platform_id: str = ""
        self.name: str = ""
        self.base_name: str = ""
        self.sound_bank_path: str = ""
        self.copied_media_path: str = ""
        self.base_display_name: str = ""

    @staticmethod
    def from_dict(data: dict) -> "WwiseProjectPlatformInfo":
        obj = WwiseProjectPlatformInfo()
        obj.platform_id = data.get("id", "")
        obj.name = data.get("name", "")
        obj.base_name = data.get("baseName", "")
        obj.sound_bank_path = data.get("soundBankPath", "")
        obj.copied_media_path = data.get("copiedMediaPath", "")
        obj.base_display_name = data.get("baseDisplayName", "")
        return obj


class WwiseProjectLanguageInfo(object):

    def __init__(self):
        self.id: str = ""
        self.short_id: int = 0
        self.name: str = ""

    @staticmethod
    def from_dict(data: dict) -> "WwiseProjectLanguageInfo":
        obj = WwiseProjectLanguageInfo()
        obj.id = data.get("id", "")
        obj.short_id = data.get("shortId", 0)
        obj.name = data.get("name", "")
        return obj


class WwiseProjectDirectoriesInfo(object):

    def __init__(self):
        self.properties: str = ""
        self.cache: str = ""
        self.root: str = ""
        self.originals: str = ""
        self.sound_bank_output_root: str = ""
        self.commands: str = ""
        self.display_title: str = ""
        self.reference_language_id: str = ""
        self.is_dirty: bool = False
        self.current_platform_id: str = ""
        self.current_language_id: str = ""
        self.default_conversion: WwiseConversionInfo = WwiseConversionInfo()

    @staticmethod
    def from_dict(data: dict) -> "WwiseProjectDirectoriesInfo":
        obj = WwiseProjectDirectoriesInfo()
        obj.properties = data.get("properties", "")
        obj.cache = data.get("cache", "")
        obj.root = data.get("root", "")
        obj.originals = data.get("originals", "")
        obj.sound_bank_output_root = data.get("soundBankOutputRoot", "")
        obj.commands = data.get("commands", "")
        obj.display_title = data.get("displayTitle", "")
        obj.reference_language_id = data.get("referenceLanguageId", "")
        obj.is_dirty = data.get("isDirty", False)
        obj.current_platform_id = data.get("currentPlatformId", "")
        obj.current_language_id = data.get("currentLanguageId", "")
        obj.default_conversion = WwiseConversionInfo.from_dict(data.get("defaultConversion", {}))
        return obj


class WwiseConversionInfo(object):

    def __init__(self):
        self.id: str = ""
        self.name: str = ""

    @staticmethod
    def from_dict(data: dict) -> "WwiseConversionInfo":
        obj = WwiseConversionInfo()
        obj.id = data.get("id", "")
        obj.name = data.get("name", "")
        return obj


class WwiseSwitchContainerAssignmentEntry(object):

    def __init__(self):
        self.child: str = ""
        self.state_or_switch: str = ""

    @staticmethod
    def from_dict(data: dict) -> "WwiseSwitchContainerAssignmentEntry":
        obj = WwiseSwitchContainerAssignmentEntry()
        obj.child = data.get("child", "")
        obj.state_or_switch = data.get("stateOrSwitch", "")
        return obj
