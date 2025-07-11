import random
from agent_network.utils.llm.chat import chat_llm
from agent_network.utils.llm.message import Message
from prompt import *

class GenActionDetails:
    # 如果安全返回不存在该区域内，则随机
    safe_sector = "kitchen"
    safe_arena = "kitchen"
    safe_object = "bed"

    safe_pronunciatio = "🙂"
    safe_triple = "idle"  # 应该为name is idle，安全返回中补充
    safe_obj_desp = "idle"  # 同上
    safe_obj_triple = "idle"

    def generate_prompt(self, curr_input, prompt_template):
        if type(curr_input) == type("string"):
            curr_input = [curr_input]
        curr_input = [str(i) for i in curr_input]
        prompt = prompt_template
        for count, i in enumerate(curr_input):
            prompt = prompt.replace(f"!<INPUT {count}>!", i)
        if "<commentblockmarker>###</commentblockmarker>" in prompt:
            prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
        return prompt.strip()
    def text_completion(self, prompt, max_tokens, clean_up, validate, safe_rsp=None):
        # 文本生成设置
        pre_prompt = f'You are a text completion model.Complete the following text in {max_tokens} tokens.Just go on and Do not repeat my final words.: \n'
        messages = [Message(role="user", content=pre_prompt + prompt)]
        result = safe_rsp
        try:
            gpt_rsp = chat_llm(messages, max_tokens=max_tokens).content
            # 验证是否通过
            if validate(gpt_rsp):
                result = clean_up(gpt_rsp)
        except Exception as e:
            pass
        return result
    def chat_completion(self, prompt, max_tokens, clean_up, validate, safe_rsp=None):
        # 对话生成设置
        messages = [Message(role="user", content=prompt)]
        result = safe_rsp
        try:
            gpt_rsp = chat_llm(messages, max_tokens=max_tokens)
            # 验证是否通过
            if validate(gpt_rsp):
                result = clean_up(gpt_rsp)
        except Exception as e:
            pass
        return result
    def generate_sector_safe(self, scratch, spatial_memory, access_tile: dict[str, str], act_desp: str):
        def __func_clean_up(gpt_rsp):
            clean_rsp = gpt_rsp.split("}")[0]
            return clean_rsp
        def __func_validate(gpt_rsp):
            if len(gpt_rsp.strip()) < 1 or "}" not in gpt_rsp or "," in gpt_rsp:
                return False
            else:
                return True
        # 1.生成prompt
        act_world = f"{access_tile['world']}"
        prompt_input = []
        prompt_input += [scratch.get_str_name()]
        prompt_input += [scratch.living_area.split(":")[1]]
        x = f"{act_world}:{scratch.living_area.split(':')[1]}"
        prompt_input += [spatial_memory.get_str_accessible_sector_arenas(x)]
        prompt_input += [scratch.get_str_name()]
        prompt_input += [f"{access_tile['sector']}"]
        x = f"{act_world}:{access_tile['sector']}"
        prompt_input += [spatial_memory.get_str_accessible_sector_arenas(x)]
        if scratch.get_str_daily_plan_req() != "":
            prompt_input += [f"\n{scratch.get_str_daily_plan_req()}"]
        else:
            prompt_input += [""]
        accessible_sector_str = spatial_memory.get_str_accessible_sectors(act_world)
        curr = accessible_sector_str.split(", ")
        fin_accessible_sectors = []
        for i in curr:
            if "'s house" in i:
                if scratch.last_name in i:
                    fin_accessible_sectors += [i]
            else:
                fin_accessible_sectors += [i]
        accessible_sector_str = ", ".join(fin_accessible_sectors)
        prompt_input += [accessible_sector_str]
        action_description_1 = act_desp
        action_description_2 = act_desp
        if "(" in act_desp:
            action_description_1 = act_desp.split("(")[0].strip()
            action_description_2 = act_desp.split("(")[-1][:-1]
        prompt_input += [scratch.get_str_name()]
        prompt_input += [action_description_1]
        prompt_input += [action_description_2]
        prompt_input += [scratch.get_str_name()]

        # 2.填入prompt
        prompt = self.generate_prompt(prompt_input, action_location_sector)

        # 3.调用大模型以及安全检查
        output = self.text_completion(prompt, max_tokens=15, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=self.safe_sector)
        y = f"{act_world}"
        x = [i.strip() for i in spatial_memory.get_str_accessible_sectors(y).split(",")]
        if output not in x:
            # 默认返回自己家
            output = scratch.living_area.split(":")[1]
        return output
    def generate_arena_safe(self, scratch, spatial_memory, access_tile: dict[str, str], act_desp: str, act_sector: str):
        def __func_clean_up(gpt_rsp):
            clean_rsp = gpt_rsp.split("}")[0]
            return clean_rsp
        def __func_validate(gpt_rsp):
            if len(gpt_rsp.strip()) < 1 or "}" not in gpt_rsp or "," in gpt_rsp:
                return False
            else:
                return True
        # 1.生成prompt
        act_world = f"{access_tile['world']}"
        prompt_input = []
        prompt_input += [scratch.get_str_name()]
        x = f"{act_world}:{act_sector}"
        prompt_input += [act_sector]
        accessible_arena_str = spatial_memory.get_str_accessible_sector_arenas(x)
        curr = accessible_arena_str.split(", ")
        fin_accessible_arenas = []
        for i in curr:
            if "'s room" in i:
                if scratch.last_name in i:
                    fin_accessible_arenas += [i]
            else:
                fin_accessible_arenas += [i]
        accessible_arena_str = ", ".join(fin_accessible_arenas)
        prompt_input += [accessible_arena_str]
        action_description_1 = act_desp
        action_description_2 = act_desp
        if "(" in act_desp:
            action_description_1 = act_desp.split("(")[0].strip()
            action_description_2 = act_desp.split("(")[-1][:-1]
        prompt_input += [scratch.get_str_name()]
        prompt_input += [action_description_1]
        prompt_input += [action_description_2]
        prompt_input += [scratch.get_str_name()]
        prompt_input += [act_sector]
        prompt_input += [accessible_arena_str]

        # 2.填入prompt
        prompt = self.generate_prompt(prompt_input, action_location_arena)

        # 3.调用大模型以及安全检查
        output = self.text_completion(prompt, max_tokens=15, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=self.safe_arena)
        y = f"{act_world}:{act_sector}"
        x = [i.strip() for i in spatial_memory.get_str_accessible_sector_arenas(y).split(",")]
        if output not in x:
            # 随机选择arena
            output = random.choice(x)
        return output
    def generate_object_safe(self, spatial_memory, act_desp: str, act_address: str):
        def __func_clean_up(gpt_rsp):
            clean_rsp = gpt_rsp.strip()
            return clean_rsp
        def __func_validate(gpt_rsp):
            if len(gpt_rsp.strip()) < 1:
                return False
            else:
                return True
        # 1.生成prompt
        prompt_input = []
        if "(" in act_desp:
            act_desp = act_desp.split("(")[-1][:-1]
        prompt_input += [act_desp]
        prompt_input += [spatial_memory.get_str_accessible_arena_game_objects(act_address)]

        # 2.填入prompt
        prompt = self.generate_prompt(prompt_input, action_location_object)

        # 3.调用大模型以及安全检查
        output = self.text_completion(prompt, max_tokens=15, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=self.safe_object)
        x = [i.strip() for i in spatial_memory.get_str_accessible_arena_game_objects(act_address).split(",")]
        if output not in x:
            # 随机选择物品
            output = random.choice(x)
        return output
    def generate_pronunciatio_safe(self, act_desp: str):
        def __func_clean_up(gpt_rsp):
            cr = gpt_rsp.strip()
            if len(cr) > 3:
                cr = cr[:3]
            return cr
        def __func_validate(gpt_rsp):
            if len(gpt_rsp.strip()) < 1:
                return False
            else:
                return True
        # 1.生成prompt
        if "(" in act_desp:
            act_desp = act_desp.split("(")[-1].split(")")[0]
        prompt_input = [act_desp]

        # 2.填入prompt
        prompt = self.generate_prompt(prompt_input, action_pronunciatio)

        # 3.调用大模型以及安全检查
        output = self.chat_completion(prompt, max_tokens=5, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=self.safe_pronunciatio)
        return output
    def generate_triple_safe(self, scratch, act_desp: str):
        def __func_clean_up(gpt_rsp):
            cr = gpt_rsp.strip()
            cr = [i.strip() for i in cr.split(")")[0].split(",")]
            return cr
        def __func_validate(gpt_rsp):
            try:
                gpt_rsp = __func_clean_up(gpt_rsp)
                if len(gpt_rsp) != 2:
                    return False
            except:
                return False
            return True
        # 1.生成prompt
        if "(" in act_desp:
            act_desp = act_desp.split("(")[-1].split(")")[0]
        prompt_input = [scratch.name, act_desp, scratch.name]

        # 2.填入prompt
        prompt = self.generate_prompt(prompt_input, action_triple)

        # 3.调用大模型以及安全检查
        fail_safe = ("is", self.safe_triple)
        output = self.text_completion(prompt, max_tokens=30, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=fail_safe)
        output = (scratch.name, output[0], output[1])
        return output
    def generate_obj_desp_safe(self, scratch, act_object: str, act_desp: str):
        def __func_clean_up(gpt_rsp):
            cr = gpt_rsp.strip()
            if cr[-1] == ".": cr = cr[:-1]
            return cr
        def __func_validate(gpt_rsp):
            if len(gpt_rsp.strip()) < 1:
                return False
            return True
        # 1.生成prompt
        prompt_input = [act_object, scratch.name, act_desp, act_object, act_object]

        # 2.填入prompt
        prompt = self.generate_prompt(prompt_input, obj_desp)

        # 3.调用大模型以及安全检查
        fail_safe = f"{act_object} is {self.safe_obj_desp}"
        output = self.text_completion(prompt, max_tokens=15, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=fail_safe)
        return output
    def generate_obj_triple_safe(self, act_object: str, act_desp: str):
        def __func_clean_up(gpt_rsp):
            cr = gpt_rsp.strip()
            cr = [i.strip() for i in cr.split(")")[0].split(",")]
            return cr

        def __func_validate(gpt_rsp):
            try:
                gpt_rsp = __func_clean_up(gpt_rsp)
                if len(gpt_rsp) != 2:
                    return False
            except:
                return False
            return True

        # 1.生成prompt
        prompt_input = [act_object, act_desp, act_object]

        # 2.填入prompt
        prompt = self.generate_prompt(prompt_input, obj_triple)

        # 3.调用大模型以及安全检查
        fail_safe = ("is", self.safe_obj_triple)
        output = self.text_completion(prompt, max_tokens=30, clean_up=__func_clean_up, validate=__func_validate,
                                      safe_rsp=fail_safe)
        output = (act_object, output[0], output[1])
        return output

    # 修改成为同步函数
    def run(self, scratch, spatial_memory, act_desp: str, act_dura, access_tile):
        # cur_tile = scratch.curr_tile
        # access_tile = role.rc.env.tiles[cur_tile[1]][cur_tile[0]]
        act_world = access_tile["world"]
        # 修改生成地点的函数
        act_sector = self.generate_sector_safe(scratch, spatial_memory, access_tile, act_desp)
        act_arena = self.generate_arena_safe(scratch, spatial_memory, access_tile, act_desp, act_sector)
        act_address = f"{act_world}:{act_sector}:{act_arena}"
        if not spatial_memory.get_str_accessible_arena_game_objects(act_address):
            act_game_object = "<random>"
        else:
            act_game_object = self.generate_object_safe(spatial_memory, act_desp, act_address)
        new_address = f"{act_world}:{act_sector}:{act_arena}:{act_game_object}"
        act_pron = self.generate_pronunciatio_safe(act_desp)
        act_event = self.generate_triple_safe(scratch, act_desp)
        # Persona's actions also influence the object states. We set those up here.
        act_obj_desp = self.generate_obj_desp_safe(scratch, act_game_object, act_desp)
        act_obj_pron =self.generate_pronunciatio_safe(act_obj_desp)
        act_obj_event = self.generate_obj_triple_safe(act_game_object, act_obj_desp)
        result_dict = {
            "action_address": new_address,
            "action_duration": int(act_dura),
            "action_description": act_desp,
            "action_pronunciatio": act_pron,
            "action_event": act_event,
            "chatting_with": None,
            "chat": None,
            "chatting_with_buffer": None,
            "chatting_end_time": None,
            "act_obj_description": act_obj_desp,
            "act_obj_pronunciatio": act_obj_pron,
            "act_obj_event": act_obj_event,
        }

        return result_dict


