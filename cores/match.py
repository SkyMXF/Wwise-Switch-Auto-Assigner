from abc import abstractmethod
from tabulate import tabulate
import Levenshtein

from cores.waapi import WaapiWampClient
from cores.tfidf import SentenceIndex
from models.auto_assign_result import AutoAssignTask, AutoAssignTaskStatus
from models.config import UserConfig
from models.wwise_object import WwiseObject
from log import LOGGER


class SwitchChildrenMatcher:

    INVALID_INDEX = -1

    def __init__(
        self,
        switch_container_obj: WwiseObject,
        user_config: UserConfig,
        waapi_client: WaapiWampClient
    ):
        self.switch_container_obj: WwiseObject = switch_container_obj
        self.user_config: UserConfig = user_config
        self.waapi_client: WaapiWampClient = waapi_client

        # get switch container info
        self.switch_group_object: WwiseObject | None = None
        self.switch_object_list: list[WwiseObject] = []
        self.container_child_list: list[WwiseObject] = []
        self.assigned_child_to_switch_dict: dict[WwiseObject, WwiseObject] = {}
        self.assigned_switch_to_child_dict: dict[WwiseObject, WwiseObject] = {}

        # name replacement
        self.name_alias_dict: dict[WwiseObject, str] = {}

        # words mapping
        self.object_word_mapping: dict[WwiseObject, list[str]] = {}

        # matching matrix
        # index: (switch_index, child_index)
        self.match_score_matrix: list[list] = []
        self.min_match_score: any = None

        # assign result
        self.assign_task_dict: dict[WwiseObject, AutoAssignTask] = {}

    # get switch container info
    def query_switch_container(self):
        self.switch_group_object = None
        self.switch_object_list.clear()
        self.container_child_list.clear()
        self.assigned_child_to_switch_dict.clear()

        # get switch group
        waql = f'from object "{self.switch_container_obj.id}" select @SwitchGroupOrStateGroup'
        query_list = self.waapi_client.query_waql(waql)
        if len(query_list) == 0:
            LOGGER.error(f"Cannot get switch group for {self.switch_container_obj.name}.")
            assign_task = AutoAssignTask(self.switch_container_obj)
            assign_task.status = AutoAssignTaskStatus.SwitchGroupNotSet
            self.assign_task_dict[self.switch_container_obj] = assign_task
            return
        self.switch_group_object: WwiseObject = query_list[0]

        # get switch objects in switch group
        waql = f'from object "{self.switch_group_object.id}" select children'
        self.switch_object_list.extend(self.waapi_client.query_waql(waql))

        # get children of switch container
        waql = f'from object "{self.switch_container_obj.id}" select children'
        self.container_child_list.extend(self.waapi_client.query_waql(waql))

        # get already assigned info
        already_assigned_list = self.waapi_client.get_switch_container_assignments(
            self.switch_container_obj.id
        )
        for assigned_entry in already_assigned_list:
            switch_object = next((obj for obj in self.switch_object_list if obj.id == assigned_entry.state_or_switch), None)
            if switch_object is None:
                LOGGER.error(f"Cannot find assigned switch object {assigned_entry.state_or_switch}.")
                continue
            child_object = next((obj for obj in self.container_child_list if obj.id == assigned_entry.child), None)
            if child_object is None:
                LOGGER.error(f"Cannot find assigned child object {assigned_entry.child}.")
                continue

            self.assigned_child_to_switch_dict[child_object] = switch_object
            self.assigned_switch_to_child_dict[switch_object] = child_object

    # fulfill name_alias_dict with name replacement config
    def apply_name_alias(self):
        self.name_alias_dict.clear()
        for wwise_object in self.switch_object_list + self.container_child_list:
            alias_name = wwise_object.name
            for old_str, new_str in self.user_config.object_name_replacement.items():
                if old_str in alias_name:
                    LOGGER.debug(f"Replace {old_str} to {new_str} in {alias_name}.")
                    alias_name = alias_name.replace(old_str, new_str)
            self.name_alias_dict[wwise_object] = alias_name

    # get display name like "object_name(alias_name)" if alias_name is different from object_name
    def get_display_name(self, obj: WwiseObject) -> str:
        alias_name = self.name_alias_dict.get(obj, obj.name)
        if alias_name == obj.name:
            return alias_name
        return f"{obj.name}({alias_name})"

    # create mapping of WwiseObject -> word list
    def create_object_word_mapping(self):
        self.object_word_mapping.clear()
        for wwise_object in self.switch_object_list + self.container_child_list:
            alias_name = self.name_alias_dict.get(wwise_object, wwise_object.name)
            self.object_word_mapping[wwise_object] = alias_name.lower().split("_")

    # calculate match score matrix
    @abstractmethod
    def cal_match_score_matrix(self):
        pass

    # get matching matrix text to display
    def get_matching_matrix_text(self) -> str:
        table_data: list[list] = [
            [self.switch_object_list[switch_idx].name] + self.match_score_matrix[switch_idx]
            for switch_idx in range(len(self.switch_object_list))
        ]
        return tabulate(
            table_data,
            headers=[""] + [
                child.name for child in self.container_child_list
            ]
        )

    # assign child to best match switch
    def prepare_assign_task(self):
        for child_idx, child_obj in enumerate(self.container_child_list):

            # skip or overwrite child with assign result
            assign_task: AutoAssignTask = self.assign_task_dict.get(child_obj, None)
            if assign_task is not None:
                continue

            # create new assign result
            assign_task = AutoAssignTask(child_obj)
            self.assign_task_dict[child_obj] = assign_task

            # get best match switch index
            best_match_switch_idx = self.get_best_match_row(child_idx)
            if best_match_switch_idx == self.INVALID_INDEX:
                # no match switch found
                LOGGER.error(f"Cannot find match switch for child {child_obj.name}.")
                assign_task.status = AutoAssignTaskStatus.NoMatchSwitch
                continue
            assign_task.expect_switch_object = self.switch_object_list[best_match_switch_idx]

    # get the highest score row index of the matrix
    def get_best_match_row(self, col_idx: int) -> int:
        min_value = self.min_match_score
        best_match_idx = self.INVALID_INDEX
        for row_idx, row_score_list in enumerate(self.match_score_matrix):
            value = row_score_list[col_idx]
            if min_value is None or value > min_value:
                min_value = value
                best_match_idx = row_idx

        return best_match_idx

    # assign child to switch
    def run_assign_task(
        self,
        assign_task: AutoAssignTask,
        overwrite_unexpect: bool = False
    ) -> bool:
        if assign_task.status != AutoAssignTaskStatus.Pending:
            if not overwrite_unexpect or assign_task.status != AutoAssignTaskStatus.AlreadyAssignedUnexpect:
                # already done task
                return True

        child_obj: WwiseObject = assign_task.wwise_object
        expect_switch_obj: WwiseObject = assign_task.expect_switch_object

        # check if already assigned
        if assign_task.status == AutoAssignTaskStatus.Pending:
            assigned_switch_obj = self.assigned_child_to_switch_dict.get(child_obj, None)
            if assigned_switch_obj is not None:
                if assigned_switch_obj == expect_switch_obj:
                    # already assigned to expected switch
                    assign_task.status = AutoAssignTaskStatus.AlreadyAssignedExpected
                    LOGGER.debug(f"Child {child_obj.name} already assigned to "
                                 f"expected switch {self.get_display_name(expect_switch_obj)}.")
                    return True
                else:
                    # already assigned to unexpect switch
                    assign_task.status = AutoAssignTaskStatus.AlreadyAssignedUnexpect
                    assign_task.unexpect_switch_object = assigned_switch_obj
                    if not overwrite_unexpect:
                        LOGGER.error(f"Child {child_obj.name} already assigned to "
                                     f"unexpect switch {self.get_display_name(assigned_switch_obj)}. "
                                     f"Expect switch {self.get_display_name(expect_switch_obj)}.")
                        return False

        # remove unexpect switch assignment if overwrite_unexpect is True
        if overwrite_unexpect and assign_task.status == AutoAssignTaskStatus.AlreadyAssignedUnexpect:
            unexpect_switch_obj = assign_task.unexpect_switch_object
            result = self.waapi_client.remove_switch_container_assignment(
                child_obj.id, unexpect_switch_obj.id
            )
            if result:
                LOGGER.debug(
                    f"Removed assignment for switch {self.get_display_name(unexpect_switch_obj)} "
                    f"with child {self.get_display_name(child_obj)}."
                )
                self.assigned_child_to_switch_dict.pop(child_obj)
                self.assigned_switch_to_child_dict.pop(unexpect_switch_obj)
            else:
                LOGGER.error(
                    f"Failed to remove assignment "
                    f"for switch {self.get_display_name(unexpect_switch_obj)} "
                    f"with child {self.get_display_name(child_obj)}.")
                return False

        # assign child to switch
        result = self.waapi_client.set_switch_container_assignment(child_obj.id, expect_switch_obj.id)
        if result:
            self.assigned_child_to_switch_dict[child_obj] = expect_switch_obj
            self.assigned_switch_to_child_dict[expect_switch_obj] = child_obj
            LOGGER.debug(
                f"Assigned child {self.get_display_name(child_obj)} "
                f"to switch {self.get_display_name(expect_switch_obj)}."
            )
            assign_task.status = AutoAssignTaskStatus.Assigned
            return True

        # assign failed
        assign_task.status = AutoAssignTaskStatus.AssignFailed
        LOGGER.error(
            f"Failed to assign child {self.get_display_name(child_obj)} "
            f"to switch {self.get_display_name(expect_switch_obj)}."
        )
        return False

    # run all assign tasks
    def run_all_assign_tasks(self, overwrite_unexpect: bool = False) -> bool:
        success = True
        for assign_task in self.assign_task_dict.values():
            if not self.run_assign_task(assign_task, overwrite_unexpect):
                success = False
        return success


class SwitchChildrenTfidfMatcher(SwitchChildrenMatcher):

    # calculate match score matrix
    def cal_match_score_matrix(self):

        # create tf-idf index for switch names
        switch_name_sentence_index = SentenceIndex()
        for switch_obj in self.switch_object_list:
            word_list: list[str] = self.object_word_mapping.get(switch_obj, [])
            switch_name_sentence_index.add_sentence(switch_obj, word_list)
        switch_name_sentence_index.generate_index()

        # create tf-idf index for child names
        child_name_sentence_index = SentenceIndex()
        for child_obj in self.container_child_list:
            word_list: list[str] = self.object_word_mapping.get(child_obj, [])
            child_name_sentence_index.add_sentence(child_obj, word_list)
        child_name_sentence_index.generate_index()

        # calculate match score matrix
        self.match_score_matrix: list[list[float]] = [
            [
                switch_name_sentence_index.get_similarity(
                    self.object_word_mapping.get(child_obj, []),
                    switch_obj
                ) + child_name_sentence_index.get_similarity(
                    self.object_word_mapping.get(switch_obj, []),
                    child_obj
                )
                for child_obj in self.container_child_list
            ]
            for switch_obj in self.switch_object_list
        ]

        # set init value for min_match_score
        self.min_match_score = 1e-6


class SwitchChildrenLevenshteinMatcher(SwitchChildrenMatcher):

    # word mapping is not needed for Levenshtein matcher
    def create_object_word_mapping(self):
        pass

    # calculate match score matrix
    def cal_match_score_matrix(self):
        self.match_score_matrix: list[list[int]] = [
            [
                # use negative value to make lower distance score higher
                - self.cal_levenshtein_distance(
                    switch_obj.name,
                    child_obj.name
                )
                for child_obj in self.container_child_list
            ]
            for switch_obj in self.switch_object_list
        ]

        # set init value for min_match_score
        self.min_match_score = -1e9

    @staticmethod
    def cal_levenshtein_distance(name_a: str, name_b: str) -> int:
        name_a = name_a.lower()
        name_b = name_b.lower()
        return Levenshtein.distance(name_a, name_b)


# match every child of switch container to one switch
# words in child object name should contain every word in switch name
class SwitchChildrenInclusionMatcher(SwitchChildrenMatcher):

    def cal_match_score_matrix(self):
        # inclusion matrix element: (intersection size / switch word count, switch word count)
        # index: (switch_index, child_index)
        self.match_score_matrix: list[list[tuple[float, int]]] = [
            [
                self.calculate_inclusion_rate(
                    self.object_word_mapping[switch_obj],
                    self.object_word_mapping[child_obj]
                )
                for child_obj in self.container_child_list
            ]
            for switch_obj in self.switch_object_list
        ]

    @staticmethod
    def calculate_inclusion_rate(
        subset_list: list[str],
        superset_list: list[str],
    ) -> tuple[float, int]:
        subset_set = set(subset_list)
        superset_set = set(superset_list)
        intersection_set = subset_set & superset_set
        return len(intersection_set) / len(subset_set), len(subset_set)

    # only accept switch with 100% inclusion rate and max word count
    def get_best_match_row(self, col_idx: int) -> int:
        max_word_count = -1
        best_match_idx = self.INVALID_INDEX
        for row_idx, row_score_list in enumerate(self.match_score_matrix):
            inclusion_rate, switch_word_count = row_score_list[col_idx]
            if inclusion_rate >= 1 - 1e-6:
                if switch_word_count > max_word_count:
                    max_word_count = switch_word_count
                    best_match_idx = row_idx

        return best_match_idx
