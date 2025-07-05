# 把自己负责的部分代码迁移到这里，要求写明白自己负责的部分需要的输入输出。
import reflect_actions
import time
from metagpt.ext.stanford_town.memory.retrieve import new_agent_retrieve
from metagpt.logs import logger
import datetime
from metagpt.ext.stanford_town.utils.utils import get_embedding
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


async def reflect(agent):
    """
    反思
    args:
        eventlist: 事件列表
        thoughtslist: 思考列表
    returns:
        return_name: 总结的thoughts
    """
    focal_points = await reflect_actions.generate_focal_points(agent, 1)
    # Retrieve the relevant Nodesobject for each of the focal points.
    # <retrieved> has keys of focal points, and values of the associated Nodes.
    retrieved = new_agent_retrieve(agent, focal_points) #返回的是字典，key为focal point，value为对应的记忆列表

    # For each of the focal points, generate thoughts and save it in the
    # agent's memory.
    for focal_pt, nodes in retrieved.items():
        xx = [i.embedding_key for i in nodes]
        for xxx in xx:
            logger.info(f"Nodes retrieved for `{focal_pt}` are `{xxx}`.")

        thoughts = await reflect_actions.generate_thoughts(agent, nodes, 1)
        # 生成的是字典类型
        for thought, evidence in thoughts.items():
            created = agent.scratch.curr_time
            expiration = created + datetime.timedelta(days=30)
            s, p, o = await reflect_actions.generate_action_event_triple(agent, "(" + thought + ")")
            keywords = set([s, p, o])
            thought_poignancy = await reflect_actions.generate_poig_score(agent, "thought", thought)
            thought_embedding_pair = (thought, get_embedding(thought))

            agent.memory.add_thought(
                created, expiration, s, p, o, thought, keywords, thought_poignancy, thought_embedding_pair, evidence
            )
            logger.info(f"add thought memory: {thought}, evidence: {evidence}")
            time.sleep(2)  # avoid Rate limit
    

async def agent_reflect(agent):
    # 需要的输入:
    # importance_trigger_curr ： 当前的重要性分数
    # event_list: 事件列表
    # thought_list: 思考列表
    # chats: 对话信息
    # chat_end_time: 对话结束时间
    if reflect_actions.reflection_trigger(agent):
        await reflect(agent)
        reflect_actions.reset_trigger(agent)
    
    if agent.scratch.chatting_end_time:
        # update 10 to it's real sec_per_step value
        if agent.scratch.curr_time + datetime.timedelta(0, agent.sec_per_step) == agent.scratch.chatting_end_time:
            all_utt = ""
            if agent.scratch.chat:
                for row in agent.scratch.chat:
                    all_utt += f"{row[0]}: {row[1]}\n"

            last_chat = agent.memory.get_last_chatagentnt.scratch.chatting_with
            if last_chat:
                evidence = [last_chat.memory_id]
            else:
                logger.info(f"agentt: {agent.name} get_last_chat: {last_chat}")
                return

            planning_thought = await reflect_actions.generate_planning_thought_on_convo(agent, all_utt)
            planning_thought = f"For {agent.scratch.name}'s planning: {planning_thought}"
            logger.info(f"agentt: {agent.name} planning_thought: {planning_thought}")

            created = agent.scratch.curr_time
            expiration = created + datetime.timedelta(days=30)
            s, p, o = await reflect_actions.generate_action_event_triple(agent, planning_thought)
            keywords = set([s, p, o])
            thought_poignancy = await reflect_actions.generate_poig_score(agent, "thought", planning_thought)
            thought_embedding_pair = (planning_thought, get_embedding(planning_thought))

            agent.memory.add_thought(
                created,
                expiration,
                s,
                p,
                o,
                planning_thought,
                keywords,
                thought_poignancy,
                thought_embedding_pair,
                evidence,
            )

            memo_thought = await reflect_actions.generate_memo_on_convo(agent, all_utt)
            memo_thought = f"{agent.scratch.name} {memo_thought}"

            created = agent.scratch.curr_time
            expiration = created + datetime.timedelta(days=30)
            s, p, o = await reflect_actions.generate_action_event_triple(agent, memo_thought)
            keywords = set([s, p, o])
            thought_poignancy = await reflect_actions.generate_poig_score(agent, "thought", memo_thought)
            thought_embedding_pair = (memo_thought, get_embedding(memo_thought))

            agent.memory.add_thought(
                created,
                expiration,
                s,
                p,
                o,
                memo_thought,
                keywords,
                thought_poignancy,
                thought_embedding_pair,
                evidence,
            )
