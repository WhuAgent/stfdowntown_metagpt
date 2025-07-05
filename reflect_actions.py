import time
from metagpt.logs import logger
import openai
import yaml
from typing import Union
import re
import os
import json
yaml_path = "config/config2.yaml" 
#use_system_prompt = True  # 是否使用系统提示词

def generate_prompt_with_tmpl_filename(prompt_input: Union[str, list], tmpl_filename) -> str:
        """
        same with `generate_prompt`
        Args:
            prompt_input: the input we want to feed in (IF THERE ARE MORE THAN ONE INPUT, THIS CAN BE A LIST.)
            tmpl_filename: prompt template filename
        Returns:
            a str prompt that will be sent to LLM server.
        """
        if isinstance(prompt_input, str):
            prompt_input = [prompt_input]
        prompt_input = [str(i) for i in prompt_input]

        tmpl_filename = os.path.join("metagpt", "ext", "stanford_town", "prompts", tmpl_filename)
        f = open(tmpl_filename, "r")
        prompt = f.read()
        f.close()
        for count, i in enumerate(prompt_input):
            prompt = prompt.replace(f"!<INPUT {count}>!", i)
        if "<commentblockmarker>###</commentblockmarker>" in prompt:
            prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
        return prompt.strip()


def chat_llm(model,prompt, max_tokens=512,use_system_prompt=True):
    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config = config.get(model, {})

    messages = []
    if use_system_prompt:
        messages.append({"role": "system", "content": "You are a helpful assistant."})
    
    messages.append({"role": "user", "content": prompt})
    openai_client = openai.OpenAI(
        api_key=config.get("api_key"),
        base_url=config.get("base_url")
    )

    try:
        response = openai_client.chat.completions.create(
            model=config.get("model"),
            messages=messages,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        return content
    except Exception as e:
        logger.error(f"chat_llm error: {e}")
        return ""

def generate_prompt_with_example(prompt, example_output, special_instruction=""):
    """
    Generate a prompt with an example output and special instructions.
    
    Args:
        prompt (str): The main prompt to be sent to the LLM.
        example_output (str): An example output to guide the LLM.
        special_instruction (str): Additional instructions for the LLM.
        
    Returns:
        str: The formatted prompt ready for LLM input.
    """
    prompt = '"""\n' + prompt + '\n"""\n'
    prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
    prompt += "Example output json:\n"
    prompt += '{"output": "' + str(example_output) + '"}'
    return prompt


#generate_focal_pt_v1.txt
async def generate_focal_points(agent, n=3):
    nodes = [
        [i.last_accessed, i] for i in agent.memory.event_list + agent.memory.thought_list if "idle" not in i.embedding_key # embedding_key:str，和content内容相同
    ]
    nodes = sorted(nodes, key=lambda x: x[0])
    nodes = [i for _, i in nodes]

    statements = ""#重要的事的拼接
    for node in nodes[-1 * agent.scratch.importance_ele_n :]:
        statements += node.embedding_key + "\n"
    
    prompt_input = [statements, str(n)]

    prompt = generate_prompt_with_tmpl_filename(prompt_input, "generate_focal_pt_v1.txt")
    example_output = '["What should Jane do for lunch", "Does Jane like strawberry", "Who is Jane"]'
    special_instruction = "Output must be a list of str."
    prompt = generate_prompt_with_example(prompt, example_output, special_instruction)

    response = chat_llm("llm", prompt)
    logger.info(f"llm response in generate focal points: {response}")
    response_json = json.loads(response)
    output = response_json["output"]
    logger.info(f"Role: {agent.name} Action: generete_focal_points, output: {output}")
    return output


# insight_and_evidence_v1.txt
async def generate_thoughts(agent, nodes, n=5):
    statements = ""
    for count, node in enumerate(nodes):
        statements += f"{str(count)}. {node.embedding_key}\n"
    

    prompt_input = [statements, str(n)]
    prompt = generate_prompt_with_tmpl_filename(prompt_input, "insight_and_evidence_v2.txt")
    
    llm_resp = chat_llm("llm", prompt,max_tokens=150,use_system_prompt=False)
    logger.info(f"llm response in generate thoughts: {llm_resp}")
    try:
        output = json.loads(llm_resp)
    except json.JSONDecodeError:
        output = {"this is blank": [0]}
    logger.info(f"Role: {agent.name} Action: generate_thoughts, output: {output}")    
    return output


async def generate_action_event_triple(agent, act_desp: str):
    if "(" in act_desp:
        act_desp = act_desp.split("(")[-1].split(")")[0]
    prompt_input = [agent.scratch.name, act_desp, agent.scratch.name]

    prompt = generate_prompt_with_tmpl_filename(prompt_input, "generate_event_triple_v2.txt")
    response = chat_llm("deepseek",prompt, max_tokens=30)
    response = response.strip()
    logger.info(f"llm response in generate triple: {response}")
    try:
        # 先尝试解析为JSON
        data = json.loads(response)
        if all(k in data for k in ("subject", "predicate", "object")):
            result = (data["subject"], data["predicate"], data["object"])
    except Exception:
        result = ("", "", "")
        match = re.search(r"\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)", response)
        if match:
            result = tuple(s.strip() for s in match.groups())
    # match = re.match(r"\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)", response)
    # if match:
    #     predicate = match.group(2).strip()
    #     obj = match.group(3).strip()
    #     result = (agent.scratch.name, predicate, obj)
    # else:
    #     result = ("", "", "")
    logger.info(f"Role: {agent.scratch.name} Action: generate_action_event_triple, output: {result}")
    return result

# planning_thought_on_convo_v1.txt
async def generate_planning_thought(agent, all_chats):
    prompt_input = [all_chats, agent.scratch.name, agent.scratch.name, agent.scratch.name]
    prompt = generate_prompt_with_tmpl_filename(prompt_input, "planning_thought_on_convo_v1.txt")

    response = chat_llm(prompt)
    response = response.split('"')[0].strip()
    logger.info(f"Role: {agent.name} Action: generate_planning, output: {response}")
    return response

# memo_on_convo_v1.txt
async def generate_memo(agent, all_chats):
    prompt_input = [all_chats, agent.scratch.name, agent.scratch.name, agent.scratch.name]
    prompt = generate_prompt_with_tmpl_filename(prompt_input, "memo_on_convo_v1.txt")

    example_output = "Jane Doe was interesting to talk to."
    special_instruction = (
        "The output should ONLY contain a string that summarizes anything interesting "
        "that the agent may have noticed"
    )
    prompt = generate_prompt_with_example(prompt, example_output, special_instruction)

    response = chat_llm("llm", prompt)
    response = response.split('"')[0].strip()
    logger.info(f"Role: {agent.name} Action: generate_memo, output: {response}")
    return response


# poignancy_event_v1.txt
async def generate_poig_score(role, event_type, description):
    if "is idle" in description:
        return 1

    prompt_input = [role.scratch.name, role.scratch.get_str_iss(), role.scratch.name, description]
    example_output = "5"  
    special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."
    if event_type == "event" or event_type == "thought":
        prompt = generate_prompt_with_tmpl_filename(prompt_input, "poignancy_event_v1.txt")

        prompt = generate_prompt_with_example(prompt, example_output, special_instruction)
        response = chat_llm("llm", prompt)
        #response = int(response.strip())
        try:
            # 尝试解析为 JSON
            data = json.loads(response.strip())
            value = data.get("output", "1")
            response = int(value)
        except Exception:
            # fallback: 直接转 int
            try:
                response = int(response.strip())
            except Exception:
                response = 1
        logger.info(f"Role: {role.name} Action: event_poignancy, output: {response}")
    elif event_type == "chat":
        prompt = generate_prompt_with_tmpl_filename(prompt_input, "poignancy_chat_v1.txt")

        prompt = generate_prompt_with_example(prompt, example_output, special_instruction)
        response = chat_llm("llm", prompt)
        try:
            # 尝试解析为 JSON
            data = json.loads(response.strip())
            value = data.get("output", "1")
            response = int(value)
        except Exception:
            # fallback: 直接转 int
            try:
                response = int(response.strip())
            except Exception:
                response = 1
        logger.info(f"Role: {role.name} Action: chat_poignancy, output: {response}")
    
    return response




def reflection_trigger(agent):
    if agent.scratch.importance_trigger_curr <= 0 and [] != agent.memory.event_list + agent.memory.thought_list:
        return True
    return False


def reset_trigger(agent):
    """
    Reset the reflection trigger for the agent.
    
    Args:
        agent: The agent whose reflection trigger is to be reset.
    """
    role_imt_max = agent.scratch.importance_trigger_max
    agent.scratch.importance_trigger_curr = role_imt_max
    agent.scratch.importance_ele_n = 0