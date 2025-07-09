from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Union
from pydantic import BaseModel, Field, field_serializer, field_validator, model_validator

from metagpt.logs import logger
from metagpt.memory.memory import Memory
from metagpt.schema import Message
from metagpt.utils.common import read_json_file, write_json_file


class Scratch(BaseModel):
    # 类别1:人物超参
    vision_r: int = 4
    att_bandwidth: int = 3
    retention: int = 5

    # 类别2:世界信息
    curr_time: Optional[datetime] = Field(default=None)
    curr_tile: Optional[list[int]] = Field(default=None)
    daily_plan_req: Optional[str] = Field(default=None)

    # 类别3:人物角色的核心身份
    name: Optional[str] = Field(default=None)
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    age: Optional[int] = Field(default=None)
    innate: Optional[str] = Field(default=None)  # L0 permanent core traits.
    learned: Optional[str] = Field(default=None)  # L1 stable traits.
    currently: Optional[str] = Field(default=None)  # L2 external implementation.
    lifestyle: Optional[str] = Field(default=None)
    living_area: Optional[str] = Field(default=None)

    # 类别4:旧反思变量
    concept_forget: int = 100
    daily_reflection_time: int = 60 * 3
    daily_reflection_size: int = 5
    overlap_reflect_th: int = 2
    kw_strg_event_reflect_th: int = 4
    kw_strg_thought_reflect_th: int = 4

    # 类别5:新反思变量
    recency_w: int = 1
    relevance_w: int = 1
    importance_w: int = 1
    recency_decay: float = 0.99
    importance_trigger_max: int = 150
    importance_trigger_curr: int = 150
    importance_ele_n: int = 0
    thought_count: int = 5

    # 类别6:个人计划
    daily_req: list[str] = Field(default=[])
    f_daily_schedule: list[list[Union[int, str]]] = Field(default=[])
    f_daily_schedule_hourly_org: list[list[Union[int, str]]] = Field(default=[])

    # 类别7:当前动作
    act_address: Optional[str] = Field(default=None)
    act_start_time: Optional[datetime] = Field(default=None)
    act_duration: Optional[int] = Field(default=None)
    act_description: Optional[str] = Field(default=None)
    act_pronunciatio: Optional[str] = Field(default=None)
    act_event: list[Optional[str]] = [None, None, None]

    act_obj_description: Optional[str] = Field(default=None)
    act_obj_pronunciatio: Optional[str] = Field(default=None)
    act_obj_event: list[Optional[str]] = [None, None, None]

    chatting_with: Optional[str] = Field(default=None)
    chat: Optional[str] = Field(default=None)
    chatting_with_buffer: dict = dict()
    chatting_end_time: Optional[datetime] = Field(default=None)

    act_path_set: bool = False
    planned_path: list[list[int]] = Field(default=[])

    @field_validator("curr_time", "act_start_time", "chatting_end_time", mode="before")
    @classmethod
    def check_time_filed(cls, time_filed):
        val = datetime.strptime(time_filed, "%B %d, %Y, %H:%M:%S") if time_filed else None
        return val

    @field_serializer("curr_time", "act_start_time", "chatting_end_time")
    def transform_time_field(self, time_filed: Optional[datetime]) -> str:
        if time_filed:
            time_filed = time_filed.strftime("%B %d, %Y, %H:%M:%S")
        return time_filed

    @classmethod
    def init_scratch_from_path(cls, f_saved: Path):
        scratch_load = read_json_file(f_saved)
        scratch = Scratch(**scratch_load)
        return scratch

    def save(self, out_json: Path):
        """
        Save persona's scratch.

        INPUT:
          out_json: The file where we wil be saving our persona's state.
        OUTPUT:
          None
        """
        scratch = self.model_dump()
        write_json_file(out_json, scratch, encoding="utf-8")

    def get_f_daily_schedule_index(self, advance=0):
        """
        We get the current index of self.f_daily_schedule.

        Recall that self.f_daily_schedule stores the decomposed action sequences
        up until now, and the hourly sequences of the future action for the rest
        of today. Given that self.f_daily_schedule is a list of list where the
        inner list is composed of [task, duration], we continue to add up the
        duration until we reach "if elapsed > today_min_elapsed" condition. The
        index where we stop is the index we will return.

        INPUT
          advance: Integer value of the number minutes we want to look into the
                   future. This allows us to get the index of a future timeframe.
        OUTPUT
          an integer value for the current index of f_daily_schedule.
        """
        # We first calculate teh number of minutes elapsed today.
        today_min_elapsed = 0
        today_min_elapsed += self.curr_time.hour * 60
        today_min_elapsed += self.curr_time.minute
        today_min_elapsed += advance

        x = 0
        for task, duration in self.f_daily_schedule:
            x += duration
        x = 0
        for task, duration in self.f_daily_schedule_hourly_org:
            x += duration

        # We then calculate the current index based on that.
        curr_index = 0
        elapsed = 0
        for task, duration in self.f_daily_schedule:
            elapsed += duration
            if elapsed > today_min_elapsed:
                return curr_index
            curr_index += 1

        return curr_index

    def get_f_daily_schedule_hourly_org_index(self, advance=0):
        """
        We get the current index of self.f_daily_schedule_hourly_org.
        It is otherwise the same as get_f_daily_schedule_index.

        INPUT
          advance: Integer value of the number minutes we want to look into the
                   future. This allows us to get the index of a future timeframe.
        OUTPUT
          an integer value for the current index of f_daily_schedule.
        """
        # We first calculate teh number of minutes elapsed today.
        today_min_elapsed = 0
        today_min_elapsed += self.curr_time.hour * 60
        today_min_elapsed += self.curr_time.minute
        today_min_elapsed += advance
        # We then calculate the current index based on that.
        curr_index = 0
        elapsed = 0
        for task, duration in self.f_daily_schedule_hourly_org:
            elapsed += duration
            if elapsed > today_min_elapsed:
                return curr_index
            curr_index += 1
        return curr_index

    def get_str_iss(self):
        """
        ISS stands for "identity stable set." This describes the commonset summary
        of this persona -- basically, the bare minimum description of the persona
        that gets used in almost all prompts that need to call on the persona.

        INPUT
          None
        OUTPUT
          the identity stable set summary of the persona in a string form.
        EXAMPLE STR OUTPUT
          "Name: Dolores Heitmiller
           Age: 28
           Innate traits: hard-edged, independent, loyal
           Learned traits: Dolores is a painter who wants live quietly and paint
             while enjoying her everyday life.
           Currently: Dolores is preparing for her first solo show. She mostly
             works from home.
           Lifestyle: Dolores goes to bed around 11pm, sleeps for 7 hours, eats
             dinner around 6pm.
           Daily plan requirement: Dolores is planning to stay at home all day and
             never go out."
        """
        commonset = ""
        commonset += f"Name: {self.name}\n"
        commonset += f"Age: {self.age}\n"
        commonset += f"Innate traits: {self.innate}\n"
        commonset += f"Learned traits: {self.learned}\n"
        commonset += f"Currently: {self.currently}\n"
        commonset += f"Lifestyle: {self.lifestyle}\n"
        commonset += f"Daily plan requirement: {self.daily_plan_req}\n"
        commonset += f"Current Date: {self.curr_time.strftime('%A %B %d') if self.curr_time else ''}\n"
        return commonset

    def get_str_name(self):
        return self.name

    def get_str_firstname(self):
        return self.first_name

    def get_str_lastname(self):
        return self.last_name

    def get_str_age(self):
        return str(self.age)

    def get_str_innate(self):
        return self.innate

    def get_str_learned(self):
        return self.learned

    def get_str_currently(self):
        return self.currently

    def get_str_lifestyle(self):
        return self.lifestyle

    def get_str_daily_plan_req(self):
        return self.daily_plan_req

    def get_str_curr_date_str(self):
        return self.curr_time.strftime("%A %B %d")

    def get_curr_event(self):
        if not self.act_address:
            return self.name, None, None
        else:
            return self.act_event

    def get_curr_event_and_desc(self):
        if not self.act_address:
            return self.name, None, None, None
        else:
            return self.act_event[0], self.act_event[1], self.act_event[2], self.act_description

    def get_curr_obj_event_and_desc(self):
        if not self.act_address:
            return "", None, None, None
        else:
            return self.act_address, self.act_obj_event[1], self.act_obj_event[2], self.act_obj_description

    def add_new_action(
        self,
        action_address,
        action_duration,
        action_description,
        action_pronunciatio,
        action_event,
        chatting_with,
        chat,
        chatting_with_buffer,
        chatting_end_time,
        act_obj_description,
        act_obj_pronunciatio,
        act_obj_event,
        act_start_time=None,
    ):
        self.act_address = action_address
        self.act_duration = action_duration
        self.act_description = action_description
        self.act_pronunciatio = action_pronunciatio
        self.act_event = action_event

        self.chatting_with = chatting_with
        self.chat = chat
        if chatting_with_buffer:
            self.chatting_with_buffer.update(chatting_with_buffer)
        self.chatting_end_time = chatting_end_time

        self.act_obj_description = act_obj_description
        self.act_obj_pronunciatio = act_obj_pronunciatio
        self.act_obj_event = act_obj_event

        self.act_start_time = self.curr_time

        self.act_path_set = False

    def act_time_str(self):
        """
        Returns a string output of the current time.

        INPUT
          None
        OUTPUT
          A string output of the current time.
        EXAMPLE STR OUTPUT
          "14:05 P.M."
        """
        return self.act_start_time.strftime("%H:%M %p")

    def act_check_finished(self):
        """
        Checks whether the self.Action instance has finished.

        INPUT
          curr_datetime: Current time. If current time is later than the action's
                         start time + its duration, then the action has finished.
        OUTPUT
          Boolean [True]: Action has finished.
          Boolean [False]: Action has not finished and is still ongoing.
        """
        if not self.act_address:
            return True

        if self.chatting_with:
            end_time = self.chatting_end_time
        else:
            x = self.act_start_time
            if x.second != 0:
                x = x.replace(second=0)
                x = x + timedelta(minutes=1)
            end_time = x + timedelta(minutes=self.act_duration)

        if end_time.strftime("%H:%M:%S") == self.curr_time.strftime("%H:%M:%S"):
            return True
        return False

    def act_summarize(self):
        """
        Summarize the current action as a dictionary.

        INPUT
          None
        OUTPUT
          ret: A human readable summary of the action.
        """
        exp = dict()
        exp["persona"] = self.name
        exp["address"] = self.act_address
        exp["start_datetime"] = self.act_start_time
        exp["duration"] = self.act_duration
        exp["description"] = self.act_description
        exp["pronunciatio"] = self.act_pronunciatio
        return exp

    def act_summary_str(self):
        """
        Returns a string summary of the current action. Meant to be
        human-readable.

        INPUT
          None
        OUTPUT
          ret: A human readable summary of the action.
        """
        start_datetime_str = self.act_start_time.strftime("%A %B %d -- %H:%M %p")
        ret = f"[{start_datetime_str}]\n"
        ret += f"Activity: {self.name} is {self.act_description}\n"
        ret += f"Address: {self.act_address}\n"
        ret += f"Duration in minutes (e.g., x min): {str(self.act_duration)} min\n"
        return ret

    def get_daily_schedule(self, daily_schedule: list[list[str]]):
        ret = ""
        curr_min_sum = 0
        for row in daily_schedule:
            curr_min_sum += row[1]
            hour = int(curr_min_sum / 60)
            minute = curr_min_sum % 60
            ret += f"{hour:02}:{minute:02} || {row[0]}\n"
        return ret

    def get_str_daily_schedule_summary(self):
        return self.get_daily_schedule(self.f_daily_schedule)

    def get_str_daily_schedule_hourly_org_summary(self):
        return self.get_daily_schedule(self.f_daily_schedule_hourly_org)


class BasicMemory(Message):
    """
    BasicMemory继承于MG的Message类，其中content属性替代description属性
    Message类中对于Chat类型支持的非常好，对于Agent个体的Perceive,Reflection,Plan支持的并不多
    在Type设计上，我们延续GA的三个种类，但是对于Chat种类的对话进行特别设计（具体怎么设计还没想好）
    """

    memory_id: Optional[str] = Field(default=None)  # 记忆ID
    memory_count: int = -1  # 第几个记忆，实际数值与Memory相等
    type_count: int = -1  # 第几种记忆，类型为整数
    memory_type: Optional[str] = Field(default=None)  # 记忆类型，包含 event,thought,chat三种类型
    depth: int = -1  # 记忆深度，类型为整数
    created: Optional[datetime] = Field(default=None)  # 创建时间
    expiration: Optional[datetime] = Field(default=None)  # 记忆失效时间，默认为空（）
    last_accessed: Optional[datetime] = Field(default=None)  # 上一次调用的时间，初始化时候与self.created一致
    subject: Optional[str] = Field(default=None)  # 主语
    predicate: Optional[str] = Field(default=None)  # 谓语
    object: Optional[str] = Field(default=None)  # 宾语

    description: Optional[str] = Field(default=None)
    embedding_key: Optional[str] = Field(default=None)  # 内容与self.content一致
    poignancy: int = -1  # importance值
    keywords: list[str] = Field(default=[])  # keywords
    filling: list = Field(default=[])  # 装的与之相关联的memory_id的列表

    __hash__ = object.__hash__  # support hash in AgentMemory

    @model_validator(mode="before")
    @classmethod
    def check_values(cls, values):
        if "created" in values:
            values["last_accessed"] = values["created"]
        if "content" in values:
            values["description"] = values["content"]
        if "filling" in values:
            values["filling"] = values["filling"] or []
        return values

    @field_serializer("created", "expiration")
    def transform_time_field(self, time_field: Optional[datetime]) -> str:
        if time_field:
            time_field = time_field.strftime("%Y-%m-%d %H:%M:%S")
        return time_field

    def summary(self):
        return self.subject, self.predicate, self.object

    def save_to_dict(self) -> dict:
        """
        将MemoryBasic类转化为字典，用于存储json文件
        这里需要注意，cause_by跟GA不兼容，所以需要做一个格式转换
        """
        memory_dict = dict()
        node_id = self.memory_id
        basic_mem_obj = self.model_dump(
            include=[
                "node_count",
                "type_count",
                "type",
                "depth",
                "created",
                "expiration",
                "subject",
                "predicate",
                "object",
                "description",
                "embedding_key",
                "poignancy",
                "keywords",
                "filling",
                "cause_by",
            ]
        )

        memory_dict[node_id] = basic_mem_obj
        return memory_dict


class AgentMemory(Memory):
    """
    GA中主要存储三种JSON
    1. embedding.json (Dict embedding_key:embedding)
    2. Node.json (Dict Node_id:Node)
    3. kw_strength.json
    """

    storage: list[BasicMemory] = []  # 重写Storage，存储BasicMemory所有节点
    event_list: list[BasicMemory] = []  # 存储event记忆
    thought_list: list[BasicMemory] = []  # 存储thought记忆
    chat_list: list[BasicMemory] = []  # chat-related memory

    event_keywords: dict[str, list[BasicMemory]] = dict()  # 存储keywords
    thought_keywords: dict[str, list[BasicMemory]] = dict()
    chat_keywords: dict[str, list[BasicMemory]] = dict()

    kw_strength_event: dict[str, int] = dict()
    kw_strength_thought: dict[str, int] = dict()

    memory_saved: Optional[Path] = Field(default=None)
    embeddings: dict[str, list[float]] = dict()

    def set_mem_path(self, memory_saved: Path):
        self.memory_saved = memory_saved
        self.load(memory_saved)

    def save(self, memory_saved: Path):
        """
        将MemoryBasic类存储为Nodes.json形式。复现GA中的Kw Strength.json形式
        这里添加一个路径即可
        TODO 这里在存储时候进行倒序存储，之后需要验证（test_memory通过）
        """
        memory_json = dict()
        for i in range(len(self.storage)):
            memory_node = self.storage[len(self.storage) - i - 1]
            memory_node = memory_node.save_to_dict()
            memory_json.update(memory_node)
        write_json_file(memory_saved.joinpath("nodes.json"), memory_json)
        write_json_file(memory_saved.joinpath("embeddings.json"), self.embeddings)

        strength_json = dict()
        strength_json["kw_strength_event"] = self.kw_strength_event
        strength_json["kw_strength_thought"] = self.kw_strength_thought
        write_json_file(memory_saved.joinpath("kw_strength.json"), strength_json)

    def load(self, memory_saved: Path):
        """
        将GA的JSON解析，填充到AgentMemory类之中
        """
        self.embeddings = read_json_file(memory_saved.joinpath("embeddings.json"))
        memory_load = read_json_file(memory_saved.joinpath("nodes.json"))
        for count in range(len(memory_load.keys())):
            node_id = f"node_{str(count + 1)}"
            node_details = memory_load[node_id]
            node_type = node_details["type"]
            created = datetime.strptime(node_details["created"], "%Y-%m-%d %H:%M:%S")
            expiration = None
            if node_details["expiration"]:
                expiration = datetime.strptime(node_details["expiration"], "%Y-%m-%d %H:%M:%S")

            s = node_details["subject"]
            p = node_details["predicate"]
            o = node_details["object"]

            description = node_details["description"]
            embedding_pair = (node_details["embedding_key"], self.embeddings[node_details["embedding_key"]])
            poignancy = node_details["poignancy"]
            keywords = set(node_details["keywords"])
            filling = node_details["filling"]
            if node_type == "thought":
                self.add_thought(
                    created, expiration, s, p, o, description, keywords, poignancy, embedding_pair, filling
                )
            if node_type == "event":
                self.add_event(created, expiration, s, p, o, description, keywords, poignancy, embedding_pair, filling)
            if node_type == "chat":
                self.add_chat(created, expiration, s, p, o, description, keywords, poignancy, embedding_pair, filling)

        strength_keywords_load = read_json_file(memory_saved.joinpath("kw_strength.json"))
        if strength_keywords_load["kw_strength_event"]:
            self.kw_strength_event = strength_keywords_load["kw_strength_event"]
        if strength_keywords_load["kw_strength_thought"]:
            self.kw_strength_thought = strength_keywords_load["kw_strength_thought"]

    def add(self, memory_basic: BasicMemory):
        """
        Add a new message to storage, while updating the index
        重写add方法，修改原有的Message类为BasicMemory类，并添加不同的记忆类型添加方式
        """
        if memory_basic.memory_id in self.storage:
            return
        self.storage.append(memory_basic)
        if memory_basic.memory_type == "chat":
            self.chat_list[0:0] = [memory_basic]
            return
        if memory_basic.memory_type == "thought":
            self.thought_list[0:0] = [memory_basic]
            return
        if memory_basic.memory_type == "event":
            self.event_list[0:0] = [memory_basic]
            return

    def add_chat(
        self, created, expiration, s, p, o, content, keywords, poignancy, embedding_pair, filling, cause_by=""
    ):
        """
        调用add方法，初始化chat，在创建的时候就需要调用embedding函数
        """
        memory_count = len(self.storage) + 1
        type_count = len(self.thought_list) + 1
        memory_type = "chat"
        memory_id = f"node_{str(memory_count)}"
        depth = 1

        memory_node = BasicMemory(
            memory_id=memory_id,
            memory_count=memory_count,
            type_count=type_count,
            memory_type=memory_type,
            depth=depth,
            created=created,
            expiration=expiration,
            subject=s,
            predicate=p,
            object=o,
            description=content,
            embedding_key=embedding_pair[0],
            poignancy=poignancy,
            keywords=keywords,
            filling=filling,
            cause_by=cause_by,
        )

        keywords = [i.lower() for i in keywords]
        for kw in keywords:
            if kw in self.chat_keywords:
                self.chat_keywords[kw][0:0] = [memory_node]
            else:
                self.chat_keywords[kw] = [memory_node]

        self.add(memory_node)

        self.embeddings[embedding_pair[0]] = embedding_pair[1]
        return memory_node

    def add_thought(self, created, expiration, s, p, o, content, keywords, poignancy, embedding_pair, filling):
        """
        调用add方法，初始化thought
        """
        memory_count = len(self.storage) + 1
        type_count = len(self.thought_list) + 1
        memory_type = "thought"
        memory_id = f"node_{str(memory_count)}"
        depth = 1

        try:
            if filling:
                depth_list = [memory_node.depth for memory_node in self.storage if memory_node.memory_id in filling]
                depth += max(depth_list)
        except Exception as exp:
            logger.warning(f"filling init occur {exp}")
            pass

        memory_node = BasicMemory(
            memory_id=memory_id,
            memory_count=memory_count,
            type_count=type_count,
            memory_type=memory_type,
            depth=depth,
            created=created,
            expiration=expiration,
            subject=s,
            predicate=p,
            object=o,
            description=content,
            embedding_key=embedding_pair[0],
            poignancy=poignancy,
            keywords=keywords,
            filling=filling,
        )

        keywords = [i.lower() for i in keywords]
        for kw in keywords:
            if kw in self.thought_keywords:
                self.thought_keywords[kw][0:0] = [memory_node]
            else:
                self.thought_keywords[kw] = [memory_node]

        self.add(memory_node)

        if f"{p} {o}" != "is idle":
            for kw in keywords:
                if kw in self.kw_strength_thought:
                    self.kw_strength_thought[kw] += 1
                else:
                    self.kw_strength_thought[kw] = 1

        self.embeddings[embedding_pair[0]] = embedding_pair[1]
        return memory_node

    def add_event(self, created, expiration, s, p, o, content, keywords, poignancy, embedding_pair, filling):
        """
        调用add方法，初始化event
        """
        memory_count = len(self.storage) + 1
        type_count = len(self.event_list) + 1
        memory_type = "event"
        memory_id = f"node_{str(memory_count)}"
        depth = 0

        if "(" in content:
            content = " ".join(content.split()[:3]) + " " + content.split("(")[-1][:-1]

        memory_node = BasicMemory(
            memory_id=memory_id,
            memory_count=memory_count,
            type_count=type_count,
            memory_type=memory_type,
            depth=depth,
            created=created,
            expiration=expiration,
            subject=s,
            predicate=p,
            object=o,
            description=content,
            embedding_key=embedding_pair[0],
            poignancy=poignancy,
            keywords=keywords,
            filling=filling,
        )

        keywords = [i.lower() for i in keywords]
        for kw in keywords:
            if kw in self.event_keywords:
                self.event_keywords[kw][0:0] = [memory_node]
            else:
                self.event_keywords[kw] = [memory_node]

        self.add(memory_node)

        if f"{p} {o}" != "is idle":
            for kw in keywords:
                if kw in self.kw_strength_event:
                    self.kw_strength_event[kw] += 1
                else:
                    self.kw_strength_event[kw] = 1

        self.embeddings[embedding_pair[0]] = embedding_pair[1]
        return memory_node

    def get_summarized_latest_events(self, retention):
        ret_set = set()
        for e_node in self.event_list[:retention]:
            ret_set.add(e_node.summary())
        return ret_set

    def get_last_chat(self, target_role_name: str):
        if target_role_name.lower() in self.chat_keywords:
            return self.chat_keywords[target_role_name.lower()][0]
        else:
            return False

    def retrieve_relevant_thoughts(self, s_content: str, p_content: str, o_content: str) -> set:
        contents = [s_content, p_content, o_content]

        ret = []
        for i in contents:
            if i in self.thought_keywords:
                ret += self.thought_keywords[i.lower()]

        ret = set(ret)
        return ret

    def retrieve_relevant_events(self, s_content: str, p_content: str, o_content: str) -> set:
        contents = [s_content, p_content, o_content]

        ret = []
        for i in contents:
            if i in self.event_keywords:
                ret += self.event_keywords[i]

        ret = set(ret)
        return ret


class MemoryTree(BaseModel):
    tree: dict = Field(default=dict)

    def set_mem_path(self, f_saved: Path):
        self.tree = read_json_file(f_saved)

    def print_tree(self) -> None:
        def _print_tree(tree, depth):
            dash = " >" * depth
            if isinstance(tree, list):
                if tree:
                    logger.info(f"{dash} {tree}")
                return

            for key, val in tree.items():
                if key:
                    logger.info(f"{dash} {tree}")
                _print_tree(val, depth + 1)

        _print_tree(self.tree, 0)

    def save(self, out_json: Path) -> None:
        write_json_file(out_json, self.tree)

    def get_str_accessible_sectors(self, curr_world: str) -> str:
        """
        Returns a summary string of all the arenas that the persona can access
        within the current sector.

        Note that there are places a given persona cannot enter. This information
        is provided in the persona sheet. We account for this in this function.

        INPUT
          None
        OUTPUT
          A summary string of all the arenas that the persona can access.
        EXAMPLE STR OUTPUT
          "bedroom, kitchen, dining room, office, bathroom"
        """
        x = ", ".join(list(self.tree[curr_world].keys()))
        return x

    def get_str_accessible_sector_arenas(self, sector: str) -> str:
        """
        Returns a summary string of all the arenas that the persona can access
        within the current sector.

        Note that there are places a given persona cannot enter. This information
        is provided in the persona sheet. We account for this in this function.

        INPUT
          None
        OUTPUT
          A summary string of all the arenas that the persona can access.
        EXAMPLE STR OUTPUT
          "bedroom, kitchen, dining room, office, bathroom"
        """
        curr_world, curr_sector = sector.split(":")
        if not curr_sector:
            return ""
        x = ", ".join(list(self.tree[curr_world][curr_sector].keys()))
        return x

    def get_str_accessible_arena_game_objects(self, arena: str) -> str:
        """
        Get a str list of all accessible game objects that are in the arena. If
        temp_address is specified, we return the objects that are available in
        that arena, and if not, we return the objects that are in the arena our
        persona is currently in.

        INPUT
          temp_address: optional arena address
        OUTPUT
          str list of all accessible game objects in the gmae arena.
        EXAMPLE STR OUTPUT
          "phone, charger, bed, nightstand"
        """
        curr_world, curr_sector, curr_arena = arena.split(":")

        if not curr_arena:
            return ""

        try:
            x = ", ".join(list(self.tree[curr_world][curr_sector][curr_arena]))
        except Exception:
            x = ", ".join(list(self.tree[curr_world][curr_sector][curr_arena.lower()]))
        return x

    def add_tile_info(self, tile_info: dict) -> None:
        if tile_info["world"]:
            if tile_info["world"] not in self.tree:
                self.tree[tile_info["world"]] = {}
        if tile_info["sector"]:
            if tile_info["sector"] not in self.tree[tile_info["world"]]:
                self.tree[tile_info["world"]][tile_info["sector"]] = {}
        if tile_info["arena"]:
            if tile_info["arena"] not in self.tree[tile_info["world"]][tile_info["sector"]]:
                self.tree[tile_info["world"]][tile_info["sector"]][tile_info["arena"]] = []
        if tile_info["game_object"]:
            if tile_info["game_object"] not in self.tree[tile_info["world"]][tile_info["sector"]][tile_info["arena"]]:
                self.tree[tile_info["world"]][tile_info["sector"]][tile_info["arena"]] += [tile_info["game_object"]]


