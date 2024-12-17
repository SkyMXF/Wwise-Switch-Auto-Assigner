from enum import Enum
from models.wwise_object import WwiseObject


class AutoAssignTaskStatus(Enum):

    Pending = -100
    AssignFailed = -4
    SwitchGroupNotSet = -3
    NoMatchSwitch = -2
    AlreadyAssignedUnexpect = -1
    Assigned = 0
    AlreadyAssignedExpected = 1


class AutoAssignTask(object):

    def __init__(self, wwise_object: WwiseObject):
        self.wwise_object: WwiseObject = wwise_object
        self.status: AutoAssignTaskStatus = AutoAssignTaskStatus.Pending
        self.expect_switch_object: WwiseObject | None = None
        self.unexpect_switch_object: WwiseObject | None = None

    @property
    def expect_switch_name(self) -> str:
        return self.expect_switch_object.name if self.expect_switch_object is not None else ""

    @property
    def unexpected_switch_name(self) -> str:
        return self.unexpect_switch_object.name if self.unexpect_switch_object is not None else ""
