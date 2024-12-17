from waapi import WaapiClient

from log import LOGGER
from models.wwise_object import WwiseObject, WwiseProjectInfo, WwiseSwitchContainerAssignmentEntry


class WaapiWampClient(object):

    def __init__(self):
        self._waapi_client: WaapiClient | None = None

    def connect(self, url: str) -> bool:
        self._waapi_client = WaapiClient(url=url)
        if not self._waapi_client.is_connected():
            LOGGER.error("Cannot connect to WAAPI.")
            self._waapi_client = None
            return False
        return True

    def disconnect(self):
        if self._waapi_client is not None:
            self._waapi_client.disconnect()

    def get_project_info(self) -> WwiseProjectInfo | None:
        result = self._waapi_client.call("ak.wwise.core.getProjectInfo")
        if not isinstance(result, dict):
            return None
        return WwiseProjectInfo.from_dict(result)

    def query_waql(
        self,
        waql_query: str,
        return_key_list: list[str] = None
    ) -> list[WwiseObject]:
        if return_key_list is None:
            return_key_list = ["name", "id", "type", "path"]

        result = self._waapi_client.call(
            "ak.wwise.core.object.get",
            {
                "waql": waql_query,
                "options": {
                    "return": return_key_list
                }
            }
        )

        if not isinstance(result, dict) or "return" not in result:
            LOGGER.error(f"Cannot get object info by WAAPI. No return field in result.")
            return []
        object_info_list = result["return"]
        if not isinstance(object_info_list, list):
            LOGGER.error(f"Cannot get object info by WAAPI. Return field is not a list.")
            return []

        wwise_object_list: list[WwiseObject] = [
            WwiseObject.from_dict(obj_info)
            for obj_info in object_info_list
        ]

        return wwise_object_list

    def get_switch_container_assignments(self, switch_container_id: str) -> list[WwiseSwitchContainerAssignmentEntry]:
        result = self._waapi_client.call(
            "ak.wwise.core.switchContainer.getAssignments",
            {
                "id": switch_container_id
            }
        )
        if not isinstance(result, dict) or "return" not in result:
            LOGGER.error(f"Cannot get switch container assignments for {switch_container_id}.")
            return []

        assignment_list = result["return"]
        if not isinstance(assignment_list, list):
            LOGGER.error(f"Cannot get switch container assignments for {switch_container_id}. Return is not a list.")
            return []

        return [
            WwiseSwitchContainerAssignmentEntry.from_dict(assignment_data)
            for assignment_data in assignment_list
        ]

    def set_switch_container_assignment(self, child_id: str, switch_id: str) -> bool:
        result = self._waapi_client.call(
            "ak.wwise.core.switchContainer.addAssignment",
            {
                "child": child_id,
                "stateOrSwitch": switch_id
            }
        )

        # result is an empty dict if succeeded
        return isinstance(result, dict) and len(result) == 0

    def remove_switch_container_assignment(self, child_id: str, switch_id: str) -> bool:
        result = self._waapi_client.call(
            "ak.wwise.core.switchContainer.removeAssignment",
            {
                "child": child_id,
                "stateOrSwitch": switch_id
            }
        )

        # result is an empty dict if succeeded
        return isinstance(result, dict) and len(result) == 0
