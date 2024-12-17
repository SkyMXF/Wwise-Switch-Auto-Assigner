import os
import sys
import argparse

from cores.waapi import WaapiWampClient
from cores.match import SwitchChildrenMatcher, SwitchChildrenInclusionMatcher, \
    SwitchChildrenTfidfMatcher, SwitchChildrenLevenshteinMatcher
from log import LOGGER, CLEAN_LOGGER
from models.auto_assign_result import AutoAssignTask, AutoAssignTaskStatus
from models.wwise_object import WwiseObject, WwiseObjectType, WwiseProjectInfo
from models.config import UserConfig

WAAPI_PORT = 8080
WAAPI_CLIENT: WaapiWampClient | None = None

# method_name -> (method, min_value)
MATCH_METHOD: dict[str, type[SwitchChildrenMatcher]] = {
    "tfidf": SwitchChildrenTfidfMatcher,
    "levenshtein": SwitchChildrenLevenshteinMatcher,
    "inclusion": SwitchChildrenInclusionMatcher,
}


def print_assign_result(assign_result: AutoAssignTask):
    if assign_result.status.value >= AutoAssignTaskStatus.Assigned.value:
        CLEAN_LOGGER.info(f"{assign_result.status.name}: "
                          f"{assign_result.wwise_object.name} "
                          f"-> {assign_result.expect_switch_name}")
    else:
        if assign_result.status == AutoAssignTaskStatus.AlreadyAssignedUnexpect:
            CLEAN_LOGGER.error(f"{assign_result.status.name}: "
                               f"{assign_result.wwise_object.name} "
                               f"-> {assign_result.expect_switch_name} "
                               f"Unexpected assigned: {assign_result.unexpected_switch_name}")
        else:
            CLEAN_LOGGER.error(f"{assign_result.status.name}: "
                               f"{assign_result.wwise_object.name}")


def main() -> int:

    global WAAPI_CLIENT

    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_root", type=str,
                        help="Project root path to check if WAAPI is connected to the correct project.")
    parser.add_argument("--object_id", type=str, help="Object ID to handle.")
    parser.add_argument("--match_method", type=str, default="tfidf", choices=MATCH_METHOD.keys(),
                        help=f"Method to match names of switch and switch container child. "
                             f"Choices: {', '.join(MATCH_METHOD.keys())}.")
    parser.add_argument("--recursive", action="store_true", help="Handle object recursively.")
    parser.add_argument("--user_config", type=str, help="User config file path.")
    args = parser.parse_args()

    # args
    LOGGER.info("Parsing args...")
    project_root: str = args.project_root
    object_id: str = args.object_id
    recursive: bool = args.recursive
    match_method_str: str = args.match_method
    match_method_matcher: type[SwitchChildrenMatcher] = MATCH_METHOD[match_method_str]
    user_config_path: str = args.user_config
    for arg_name, arg_value in [
        ("project_root", project_root),
        ("object_id", object_id),
        ("recursive", recursive),
        ("match_method", match_method_str),
        ("user_config", user_config_path)
    ]:
        LOGGER.debug(f"{arg_name}: {arg_value}")

    # load user config
    LOGGER.info("Loading user config...")
    user_config: UserConfig = UserConfig()
    user_config.load(user_config_path)
    user_config.save(user_config_path)  # save to add new config keys if not exist

    # connect to waapi
    WAAPI_CLIENT = WaapiWampClient()
    if not WAAPI_CLIENT.connect(f"ws://127.0.0.1:{WAAPI_PORT}/waapi"):
        LOGGER.error("Cannot connect to WAAPI.")
        return -1

    # get project info by waapi
    project_info: WwiseProjectInfo = WAAPI_CLIENT.get_project_info()
    if project_info is None:
        LOGGER.error("Cannot get project info by WAAPI.")
        return -1
    project_root_waapi = project_info.directories.root
    if os.path.normpath(project_root) != os.path.normpath(project_root_waapi):
        LOGGER.error(f"Project root not match. WAAPI is connected to: {project_root_waapi}")
        return -1
    LOGGER.info(f"WAAPI is connected to project root: {project_root}.")

    # get object info by waapi
    waql = f'from project where id = "{object_id}"'
    wwise_object_list = WAAPI_CLIENT.query_waql(waql)
    if len(wwise_object_list) == 0:
        LOGGER.error(f"Object {object_id} not found with waapi.")
        return -1
    root_wwise_object = wwise_object_list[0]

    # collect switch container to be handled
    switch_container_list: list[WwiseObject] = []
    if root_wwise_object.type == WwiseObjectType.SwitchContainer:
        switch_container_list.append(root_wwise_object)
        LOGGER.debug(f"Collect root switch container: {root_wwise_object.name}")
    if recursive:
        waql = f'from object "{object_id}" select descendants where type = "SwitchContainer"'
        wwise_object_list = WAAPI_CLIENT.query_waql(waql)
        for wwise_object in wwise_object_list:
            switch_container_list.append(wwise_object)
            LOGGER.debug(f"Collect descendant switch container: {wwise_object.name}")

    # handle each switch container
    LOGGER.info(f"Start handling {len(switch_container_list)} switch containers...")
    all_assign_result_list: list[AutoAssignTask] = []
    for switch_container_object in switch_container_list:
        LOGGER.info(f"Handling switch container: {switch_container_object.name}")
        match_method_matcher_instance = match_method_matcher(
            switch_container_obj=switch_container_object,
            user_config=user_config,
            waapi_client=WAAPI_CLIENT
        )

        # generate match matrix
        match_method_matcher_instance.query_switch_container()
        match_method_matcher_instance.apply_name_alias()
        match_method_matcher_instance.create_object_word_mapping()
        match_method_matcher_instance.cal_match_score_matrix()
        matching_matrix_text = match_method_matcher_instance.get_matching_matrix_text()
        CLEAN_LOGGER.info(f"Matching matrix:\n{matching_matrix_text}")

        # run assign
        match_method_matcher_instance.prepare_assign_task()
        match_method_matcher_instance.run_all_assign_tasks()

        # check assign result
        LOGGER.info(f"Checking assign result for {switch_container_object.name}...")
        assign_task_list = sorted(
            match_method_matcher_instance.assign_task_dict.values(),
            key=lambda x: x.status.value, reverse=True
        )
        for assign_task in assign_task_list:
            print_assign_result(assign_task)

        # let user decide if overwrite non-expected assignments
        unexpected_assign_list = [
            result for result in assign_task_list
            if result.status == AutoAssignTaskStatus.AlreadyAssignedUnexpect
        ]
        if len(unexpected_assign_list) > 0:
            CLEAN_LOGGER.warning(
                f"Found {len(unexpected_assign_list)} unexpected assignments. "
                f"Overwrite them? (y/n, default: n)")
            user_input = input()
            if user_input.lower() == "y":
                match_method_matcher_instance.run_all_assign_tasks(overwrite_unexpect=True)

        all_assign_result_list.extend(assign_task_list)

    # print all assign results
    LOGGER.info("Print all assign results...")
    all_assign_result_list.sort(key=lambda x: x.status.value, reverse=True)
    assign_result_count_dict: dict[AutoAssignTaskStatus, int] = {}
    for result_type in AutoAssignTaskStatus:
        assign_result_count_dict[result_type] = 0
    for assign_task in all_assign_result_list:
        print_assign_result(assign_task)
        assign_result_count_dict[assign_task.status] += 1

    CLEAN_LOGGER.info(f"Result summary:")
    for result_type, count in assign_result_count_dict.items():
        CLEAN_LOGGER.info(f"{result_type.name}: {count}")

    return 0


if __name__ == '__main__':

    try:
        exit_code = main()
    except Exception as e:
        LOGGER.exception(e)
        exit_code = -1

    if WAAPI_CLIENT is not None:
        LOGGER.info("Disconnecting WAAPI client...")
        WAAPI_CLIENT.disconnect()

    input(f"Finished with exit code {exit_code}. Press any key to exit...")
    sys.exit(exit_code)
