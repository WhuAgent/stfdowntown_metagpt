# 把自己负责的部分代码迁移到这里，要求写明白自己负责的部分需要的输入输出。

def example(input):
    """
    描述一下这个功能模块所干的事情。
    args:
        arg_name: 参数描述
    returns:
        return_name: 输出描述
    """
    # do someting
    output = input
    return output

import random
import datetime
from typing import Any, Optional, Union
from openai import OpenAI
def _choose_retrieved(role_name: str, retrieved: dict) -> Union[None, dict]:
    """
    选择性关注周围的事件
    检索到的元素可能有多个“curr_event”，这个函数负责选择一个事件，此事件是当前人物需要做出反应的事件
    Args:
      role_name: 当前的人物名
      retrieved: 从人物社交记忆中检索到的概念（<ConceptNode>）字典，字典有以下结构：
                 dictionary[event.description] =
                   {["curr_event"] = <ConceptNode>,
                    ["events"] = [<ConceptNode>, ...],
                    ["thoughts"] = [<ConceptNode>, ...] }
    Returns:
        None | dict
        dict: {"curr_event":<ConceptNode>, "events":[<ConceptNode>,,,], "thoughts":[ConceptNode]}
    """
    # 过滤掉当前人物为主语的事件
    copy_retrieved = retrieved.copy()
    for event_desc, rel_ctx in copy_retrieved.items():
        curr_event = rel_ctx["curr_event"]
        if curr_event.subject == role_name:
            del retrieved[event_desc]

    # Always choose role first.
    priority = []
    for event_desc, rel_ctx in retrieved.items():
        curr_event = rel_ctx["curr_event"]
        # 当前事件的主语是人
        if ":" not in curr_event.subject and curr_event.subject != role_name:
            priority += [rel_ctx]
            
    # 随机选一个以人为主语事件
    if priority:
        return random.choice(priority)

    # Skip idle.
    # 跳过处于空闲状态的物品
    for event_desc, rel_ctx in retrieved.items():
        if "is idle" not in event_desc:
            priority += [rel_ctx]
    if priority:
        return random.choice(priority)
    
    # 没有事件则不关注事件
    return None


async def _should_react(role , retrieved: dict, roles: dict):
    """
    给出关注的周围的事件，判断应该以何种形式进行反馈
    Args:
        role: 主角人物类示例（“STRole”）
        retrieved: {"curr_event":<ConceptNode>, "events":[<ConceptNode>,,,], "thoughts":[ConceptNode]}
        roles: {"角色名":角色名对应的示例}
    Returns:
        False(bool) | "chat with {某个角色}" | "wait: {时间戳}"
    """

    async def lets_talk(init_role , target_role , retrieved: dict):
        # 不与自己对话
        if init_role.name == target_role.name:
            # logger.info(f"Role: {role.name} _should_react lets_talk meet same role, return False")
            return False

        # 人物动作信息
        scratch = init_role.rc.scratch
        # 对象动作信息
        target_scratch = target_role.rc.scratch
        
        # 二者信息动作信息不全
        if (
            not target_scratch.act_address
            or not target_scratch.act_description
            or not scratch.act_address
            or not scratch.act_description
        ):
            return False

        # 某一方在睡觉
        if "sleeping" in target_scratch.act_description or "sleeping" in scratch.act_description:
            return False

        # 动作时间为23点 太晚了
        if scratch.curr_time.hour == 23:
            return False

        # 对象在等待做某事 不要打扰
        if "<waiting>" in target_scratch.act_address:
            return False

        # 某一方目前正在与人交谈 不要打扰
        if target_scratch.chatting_with or scratch.chatting_with:
            return False

        # 聊天冷却期 可能不久之前才聊过天
        if target_role.name in scratch.chatting_with_buffer:
            if scratch.chatting_with_buffer[target_role.name] > 0:
                return False

        if await DecideToTalk().run(init_role, target_role, retrieved):
            return True

        return False

    async def lets_react(init_role , target_role , retrieved: dict):
        if init_role.name == target_role.name:
            # logger.info(f"Role: {role.name} _should_react lets_react meet same role, return False")
            return False

        scratch = init_role.rc.scratch
        target_scratch = target_role.rc.scratch
        # 二者信息动作信息不全
        if (
            not target_scratch.act_address
            or not target_scratch.act_description
            or not scratch.act_address
            or not scratch.act_description
        ):
            return False
        
        # 某一方在睡觉
        if "sleeping" in target_scratch.act_description or "sleeping" in scratch.act_description:
            return False

        # 动作时间为23点 太晚了
        if scratch.curr_time.hour == 23:
            return False

        # 对象在等待做某事 不要打扰
        if "waiting" in target_scratch.act_description:
            return False
        # 计划为空
        if scratch.planned_path == []:
            return False
        
        # 二者地点不一样
        if scratch.act_address != target_scratch.act_address:
            return False

        react_mode = await DecideToReact().run(init_role, target_role, retrieved)

        if react_mode == "1":
            wait_until = (
                target_scratch.act_start_time + datetime.timedelta(minutes=target_scratch.act_duration - 1)
            ).strftime("%B %d, %Y, %H:%M:%S")
            return f"wait: {wait_until}"
        elif react_mode == "2":
            return False
        else:
            return False  # "keep"

    # 如果人物当前在对话或者在等待做某事，默认不对其他事件做出反应 scratch表示角色信息类
    scratch = role.rc.scratch
    if scratch.chatting_with:
        return False
    if "<waiting>" in scratch.act_address:
        return False

    curr_event = retrieved["curr_event"]

    # 判断 curr_event 主语不是物品
    if ":" not in curr_event.subject:
        # this is a role event.
        if await lets_talk(role, roles[curr_event.subject], retrieved):
            return f"chat with {curr_event.subject}"
        react_mode = await lets_react(role, roles[curr_event.subject], retrieved)
        return react_mode
    # 如果curr_event 主语是物品，则回应形式为False
    return False

class DecideToTalk():

    def chat_llm(prompt:str):

        client = OpenAI(api_key="", base_url="")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        
        return response.choices[0].message.content

    def _func_fail_default_resp(self) -> str:
        return "yes"
    
    def generate_prompt_with_tmpl_filename(self, prompt_input: Union[str, list]) -> str:
        """
        用构建的字段替换提示词模板
        Args:
            prompt_input: 构建的字段列表
            tmpl_filename: 提示词模板文件位置
        Returns:
            与大语言模型交互的完整提示词
        """
        if isinstance(prompt_input, str):
            prompt_input = [prompt_input]
        prompt_input = [str(i) for i in prompt_input]

        prompt='''
Given context, determine whether the subject will initiate a conversation with another. Answer in "yes" or "no" without any other messages.
!<INPUT 0>! 
Right now, it is !<INPUT 1>!. !<INPUT 2>! and !<INPUT 3>! last chatted at !<INPUT 4>! about !<INPUT 5>!. 
!<INPUT 6>! 
!<INPUT 7>! 
Would !<INPUT 8>! initiate a conversation with !<INPUT 9>!? 
        '''
        for count, i in enumerate(prompt_input):
            prompt = prompt.replace(f"!<INPUT {count}>!", i)
        return prompt.strip()

    async def run(self, init_role, target_role, retrieved: dict) -> bool:
        """Run action"""

        # 构建提示词关键词
        def create_prompt_input(init_role , target_role , retrieved: dict) -> str:
            scratch = init_role.rc.scratch
            target_scratch = target_role.rc.scratch
            last_chat = init_role.rc.memory.get_last_chat(target_role.name)
            last_chatted_time = ""
            last_chat_about = ""
            if last_chat:
                last_chatted_time = last_chat.created.strftime("%B %d, %Y, %H:%M:%S")
                last_chat_about = last_chat.description

            context = ""
            for c_node in retrieved["events"]:
                curr_desc = c_node.description.split(" ")
                curr_desc[2:3] = ["was"]
                curr_desc = " ".join(curr_desc)
                context += f"{curr_desc}. "
            context += "\n"
            for c_node in retrieved["thoughts"]:
                context += f"{c_node.description}. "

            curr_time = scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
            init_act_desc = scratch.act_description
            if "(" in init_act_desc:
                init_act_desc = init_act_desc.split("(")[-1][:-1]

            if len(scratch.planned_path) == 0 and "waiting" not in init_act_desc:
                init_p_desc = f"{init_role.name} is already {init_act_desc}"
            elif "waiting" in init_act_desc:
                init_p_desc = f"{init_role.name} is {init_act_desc}"
            else:
                init_p_desc = f"{init_role.name} is on the way to {init_act_desc}"

            target_act_desc = scratch.act_description
            if "(" in target_act_desc:
                target_act_desc = target_act_desc.split("(")[-1][:-1]

            if len(target_scratch.planned_path) == 0 and "waiting" not in init_act_desc:
                target_p_desc = f"{target_role.name} is already {target_act_desc}"
            elif "waiting" in init_act_desc:
                target_p_desc = f"{init_role.name} is {init_act_desc}"
            else:
                target_p_desc = f"{target_role.name} is on the way to {target_act_desc}"

            prompt_input = []
            prompt_input += [context] # 上下文信息

            prompt_input += [curr_time] # 当前时间

            prompt_input += [init_role.name] # 主角名字
            prompt_input += [target_role.name] # 目标人选名字
            prompt_input += [last_chatted_time] # 上次交谈的时间
            prompt_input += [last_chat_about] # 上次交谈的话题

            prompt_input += [init_p_desc] # 主角状态描述
            prompt_input += [target_p_desc] # 目标人选状态描述
            prompt_input += [init_role.name] # 主角名字
            prompt_input += [target_role.name] # 目标人选名字
            return prompt_input

        prompt_input = create_prompt_input(init_role, target_role, retrieved)
        prompt = self.generate_prompt_with_tmpl_filename(
            prompt_input=prompt_input
        )
        self.fail_default_resp = self._func_fail_default_resp()
        output = await self.chat_llm(prompt)  # yes or no
        result = True if output == "yes" else False
        # logger.info(f"Role: {init_role.name} Action: {self.cls_name} output: {result}")
        return result
    
    
class DecideToReact():

    def chat_llm(prompt:str):

        client = OpenAI(api_key="", base_url="")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        
        return response.choices[0].message.content

    def _func_fail_default_resp(self) -> str:
        return "Option 2"
    
    def generate_prompt_with_tmpl_filename(self, prompt_input: Union[str, list], tmpl_filename) -> str:
        """
        用构建的字段替换提示词模板
        Args:
            prompt_input: 构建的字段列表
            tmpl_filename: 提示词模板文件位置
        Returns:
            与大语言模型交互的完整提示词
        """
        if isinstance(prompt_input, str):
            prompt_input = [prompt_input]
        prompt_input = [str(i) for i in prompt_input]

        prompt='''
Given context and three options that a subject can take, determine which option is the most acceptable. Answer in the format of Option x. Example: "Option 1"
!<INPUT 0>!
Right now, it is !<INPUT 1>!. 
!<INPUT 2>! 
!<INPUT 3>! 
Let's think step by step. Of the following two options, what should !<INPUT 4>! do?
Option 1: Wait on !<INPUT 5>! until !<INPUT 6>! is done !<INPUT 7>!
Option 2: Continue on to !<INPUT 8>! now
        '''
        for count, i in enumerate(prompt_input):
            prompt = prompt.replace(f"!<INPUT {count}>!", i)
        return prompt.strip()

    async def run(self, init_role, target_role, retrieved: dict) -> bool:
        """Run action"""

        # 构建提示词关键词
        def create_prompt_input(init_role , target_role , retrieved: dict) -> str:
            context = ""
            for c_node in retrieved["events"]: 
                curr_desc = c_node.description.split(" ")
                curr_desc[2:3] = ["was"]
                curr_desc = " ".join(curr_desc)
                context +=  f"{curr_desc}. "
            context += "\n"
            for c_node in retrieved["thoughts"]: 
                context +=  f"{c_node.description}. "

            curr_time =  init_role.scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
            init_act_desc =  init_role.scratch.act_description
            if "(" in init_act_desc: 
                init_act_desc = init_act_desc.split("(")[-1][:-1]
            if len( init_role.scratch.planned_path) == 0: 
                loc = ""
                if ":" in  init_role.scratch.act_address:
                    loc =  init_role.scratch.act_address.split(":")[-1] + " in " +  init_role.scratch.act_address.split(":")[-2]
                init_p_desc = f"{ init_role.name} is already {init_act_desc} at {loc}"
            else: 
                loc = ""
                if ":" in  init_role.scratch.act_address:
                    loc =  init_role.scratch.act_address.split(":")[-1] + " in " +  init_role.scratch.act_address.split(":")[-2]
                init_p_desc = f"{ init_role.name} is on the way to {init_act_desc} at {loc}"

            target_act_desc =  target_role.scratch.act_description
            if "(" in target_act_desc: 
                target_act_desc = target_act_desc.split("(")[-1][:-1]
            if len( target_role.scratch.planned_path) == 0: 
                loc = ""
                if ":" in  target_role.scratch.act_address:
                    loc =  target_role.scratch.act_address.split(":")[-1] + " in " +  target_role.scratch.act_address.split(":")[-2]
                target_p_desc = f"{ target_role.name} is already {target_act_desc} at {loc}"
            else: 
                loc = ""
                if ":" in  target_role.scratch.act_address:
                    loc =  target_role.scratch.act_address.split(":")[-1] + " in " +  target_role.scratch.act_address.split(":")[-2]
                target_p_desc = f"{ target_role.name} is on the way to {target_act_desc} at {loc}"

            prompt_input = []
            prompt_input += [context]# 0
            prompt_input += [curr_time]# 1
            prompt_input += [init_p_desc]# 2
            prompt_input += [target_p_desc]# 3

            prompt_input += [ init_role.name]# 4
            prompt_input += [init_act_desc]# 5
            prompt_input += [ target_role.name]# 6
            prompt_input += [target_act_desc]# 7

            prompt_input += [init_act_desc]# 8
            return prompt_input

        prompt_input = create_prompt_input(init_role, target_role, retrieved)
        prompt = self.generate_prompt_with_tmpl_filename(
            prompt_input=prompt_input
        )
        self.fail_default_resp = self._func_fail_default_resp()
        output = await self.chat_llm(prompt)  # yes or no
        if output.split("Option")[-1].strip().lower() in [ "2", "1"]:
            return output.split("Option")[-1].strip().lower()
        # logger.info(f"Role: {init_role.name} Action: {self.cls_name} output: {result}")
        return False