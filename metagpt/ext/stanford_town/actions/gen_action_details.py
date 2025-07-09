#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : gen_action_details

# my import
import json


import random

from metagpt.environment.stanford_town.env_space import EnvObsParams, EnvObsType
from metagpt.ext.stanford_town.actions.st_action import STAction
from metagpt.logs import logger


from metagpt.ext.stanford_town.utils.const import PROMPTS_DIR
from pathlib import Path


import yaml
import openai
with open("C:\\Users\\86173\\Desktop\\Agent-network\\Code\\stfdowntown_metagpt\\config\\config2.yaml") as f:
    data = yaml.safe_load(f)

class GenActionDetails():
    api_key = data['llm']['api_key']
    model = data['llm']['model']
    base_url = data['llm']['base_url']

    safe_sector = "kitchen"
    safe_arena = "kitchen"
    safe_object = "bed"
    safe_pronunciatio = "🙂"
    safe_triple = "idle"  # 应该为name is idle，函数中补充
    safe_obj_desp = "idle"  # 同上
    safe_obj_triple = "idle"

    name: str = "GenActionDetails"

    prompt_dir: Path = PROMPTS_DIR

    def generate_prompt(self, curr_input, prompt_lib_file):
        if type(curr_input) == type("string"):
            curr_input = [curr_input]
        curr_input = [str(i) for i in curr_input]
        f = open(str(self.prompt_dir.joinpath(prompt_lib_file)), "r", encoding="utf-8")
        prompt = f.read()
        f.close()
        for count, i in enumerate(curr_input):
            prompt = prompt.replace(f"!<INPUT {count}>!", i)
        if "<commentblockmarker>###</commentblockmarker>" in prompt:
            prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
        return prompt.strip()
    def chat_llm(self, messages, max_tokens):
        rsp = openai.OpenAI(base_url=self.base_url, api_key=self.api_key).chat.completions.create(
            model = self.model,
            messages=messages,
            max_tokens=max_tokens
        )
        print(rsp.choices[0].message.content+"\n")
        return rsp.choices[0].message.content
    def text_completion(self, prompt, max_tokens, clean_up, validate, safe_rsp=None):
        pre_prompt = f'You are a text completion model.Complete the following text in {max_tokens} tokens.Just go on and Do not repeat my final words.: \n'
        messages = [{'role':'user', 'content':pre_prompt + prompt}]
        result = safe_rsp
        try:
            gpt_rsp = self.chat_llm(messages, max_tokens)
            # 验证是否通过
            if validate(gpt_rsp):
                result = clean_up(gpt_rsp)
        except Exception as e:
            logger.warning(f"Action details generation failed: {e}")
        return result
    def chat_completion(self, prompt, max_tokens, clean_up, validate, safe_rsp=None):
        messages = [{'role':'user', 'content': prompt}]
        result = safe_rsp
        try:
            gpt_rsp = self.chat_llm(messages, max_tokens)
            # 验证是否通过
            if validate(gpt_rsp):
                result = clean_up(gpt_rsp)
        except Exception as e:
            logger.warning(f"Action details generation failed: {e}")
        return result
    def generate_sector_safe(self, role: "STRole", access_tile: dict[str, str], act_desp: str):
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
        prompt_input += [role.scratch.get_str_name()]
        prompt_input += [role.scratch.living_area.split(":")[1]]
        x = f"{act_world}:{role.scratch.living_area.split(':')[1]}"
        prompt_input += [role.s_mem.get_str_accessible_sector_arenas(x)]
        prompt_input += [role.scratch.get_str_name()]
        prompt_input += [f"{access_tile['sector']}"]
        x = f"{act_world}:{access_tile['sector']}"
        prompt_input += [role.s_mem.get_str_accessible_sector_arenas(x)]
        if role.scratch.get_str_daily_plan_req() != "":
            prompt_input += [f"\n{role.scratch.get_str_daily_plan_req()}"]
        else:
            prompt_input += [""]
        accessible_sector_str = role.s_mem.get_str_accessible_sectors(act_world)
        curr = accessible_sector_str.split(", ")
        fin_accessible_sectors = []
        for i in curr:
            if "'s house" in i:
                if role.scratch.last_name in i:
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
        prompt_input += [role.scratch.get_str_name()]
        prompt_input += [action_description_1]
        prompt_input += [action_description_2]
        prompt_input += [role.scratch.get_str_name()]

        # 2.填入prompt
        prompt_template = "action_location_sector_v1.txt"
        prompt = self.generate_prompt(prompt_input, prompt_template)

        # 3.调用大模型以及安全检查
        output = self.text_completion(prompt, max_tokens=15, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=self.safe_sector)
        y = f"{act_world}"
        x = [i.strip() for i in role.s_mem.get_str_accessible_sectors(y).split(",")]
        if output not in x:
            # 默认返回自己家
            output = role.scratch.living_area.split(":")[1]
        return output
    def generate_arena_safe(self, role: "STRole", access_tile: dict[str, str], act_desp: str, act_sector: str):
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
        prompt_input += [role.scratch.get_str_name()]
        x = f"{act_world}:{act_sector}"
        prompt_input += [act_sector]
        accessible_arena_str = role.s_mem.get_str_accessible_sector_arenas(x)
        curr = accessible_arena_str.split(", ")
        fin_accessible_arenas = []
        for i in curr:
            if "'s room" in i:
                if role.scratch.last_name in i:
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
        prompt_input += [role.scratch.get_str_name()]
        prompt_input += [action_description_1]
        prompt_input += [action_description_2]
        prompt_input += [role.scratch.get_str_name()]
        prompt_input += [act_sector]
        prompt_input += [accessible_arena_str]

        # 2.填入prompt
        prompt_template = "action_location_object_vMar11.txt"
        prompt = self.generate_prompt(prompt_input, prompt_template)

        # 3.调用大模型以及安全检查
        output = self.text_completion(prompt, max_tokens=15, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=self.safe_arena)
        y = f"{act_world}:{act_sector}"
        x = [i.strip() for i in role.s_mem.get_str_accessible_sector_arenas(y).split(",")]
        if output not in x:
            # 随机选择arena
            output = random.choice(x)
        return output
    def generate_object_safe(self, role: "STRole", act_desp: str, act_address: str):
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
        prompt_input += [role
                         .s_mem.get_str_accessible_arena_game_objects(act_address)]

        # 2.填入prompt
        prompt_template = "action_object_v2.txt"
        prompt = self.generate_prompt(prompt_input, prompt_template)

        # 3.调用大模型以及安全检查
        output = self.text_completion(prompt, max_tokens=15, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=self.safe_object)
        x = [i.strip() for i in role.s_mem.get_str_accessible_arena_game_objects(act_address).split(",")]
        if output not in x:
            output = random.choice(x)
        return output
    def generate_pronunciatio_safe(self, role: "STRole", act_desp: str):
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
        prompt_template = "generate_pronunciatio_v1.txt"
        prompt = self.generate_prompt(prompt_input, prompt_template)

        # 3.调用大模型以及安全检查
        output = self.chat_completion(prompt, max_tokens=5, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=self.safe_pronunciatio)
        return output
    def generate_triple_safe(self, role: "STRole", act_desp: str):
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
        prompt_input = [role.name, act_desp, role.name]

        # 2.填入prompt
        prompt_template = "generate_event_triple_v1.txt"
        prompt = self.generate_prompt(prompt_input, prompt_template)

        # 3.调用大模型以及安全检查
        fail_safe = ("is", self.safe_triple)
        output = self.text_completion(prompt, max_tokens=30, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=fail_safe)
        output = (role.name, output[0], output[1])
        return output
    def generate_obj_desp_safe(self, role: "STRole", act_object: str, act_desp: str):
        def __func_clean_up(gpt_rsp):
            cr = gpt_rsp.strip()
            if cr[-1] == ".": cr = cr[:-1]
            return cr
        def __func_validate(gpt_rsp):
            if len(gpt_rsp.strip()) < 1:
                return False
            return True
        # 1.生成prompt
        prompt_input = [act_object, role.name, act_desp, act_object, act_object]

        # 2.填入prompt
        prompt_template = "generate_obj_event_v1.txt"
        prompt = self.generate_prompt(prompt_input, prompt_template)

        # 3.调用大模型以及安全检查
        fail_safe = f"{act_object} is {self.safe_obj_desp}"
        output = self.text_completion(prompt, max_tokens=15, clean_up=__func_clean_up, validate=__func_validate, safe_rsp=fail_safe)
        return output
    def generate_obj_triple_safe(self, role: "STRole", act_object: str, act_desp: str):
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
        prompt_template = "generate_event_triple_v1.txt"
        prompt = self.generate_prompt(prompt_input, prompt_template)

        # 3.调用大模型以及安全检查
        fail_safe = ("is", self.safe_obj_triple)
        output = self.text_completion(prompt, max_tokens=30, clean_up=__func_clean_up, validate=__func_validate,
                                      safe_rsp=fail_safe)
        output = (act_object, output[0], output[1])
        return output

    # 修改成为同步函数
    def run(self, role: "STRole", act_desp: str, act_dura):
        # 获取当前地点信息，以下为数据结构
        # Given(58, 9),
        # self.tiles[9][58] = {'world': 'double studio',
        #                      'sector': 'double studio', 'arena': 'bedroom 2',
        #                      'game_object': 'bed', 'spawning_location': 'bedroom-2-a',
        #                      'collision': False,
        #                      'events': {('double studio:double studio:bedroom 2:bed',
        #                                  None, None)}}
        cur_tile = role.scratch.curr_tile
        access_tile = role.rc.env.tiles[cur_tile[1]][cur_tile[0]]
        # access_tile = role.rc.env.observe(
        #     obs_params=EnvObsParams(obs_type=EnvObsType.GET_TITLE, coord=role.scratch.curr_tile)
        # )
        act_world = access_tile["world"]
        # 修改生成地点的函数
        act_sector = self.generate_sector_safe(role, access_tile, act_desp)
        act_arena = self.generate_arena_safe(role, access_tile, act_desp, act_sector)
        act_address = f"{act_world}:{act_sector}:{act_arena}"
        if not role.s_mem.get_str_accessible_arena_game_objects(act_address):
            act_game_object = "<random>"
        else:
            act_game_object = self.generate_object_safe(role, act_desp, act_address)
        new_address = f"{act_world}:{act_sector}:{act_arena}:{act_game_object}"
        act_pron = self.generate_pronunciatio_safe(role, act_desp)
        act_event = self.generate_triple_safe(role, act_desp)
        # Persona's actions also influence the object states. We set those up here.
        act_obj_desp = self.generate_obj_desp_safe(role, act_game_object, act_desp)
        act_obj_pron =self.generate_pronunciatio_safe(role, act_obj_desp)
        act_obj_event = self.generate_obj_triple_safe(role, act_game_object, act_obj_desp)
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
        logger.info(f"Role: {role.name} Action: GenActionDetails output: {result_dict}")
        # 将结果写入文件查看
        with open('data_pretty.json', 'w') as f:
            json.dump(result_dict, f, indent=4)

        return result_dict
