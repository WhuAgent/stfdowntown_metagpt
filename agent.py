from openai import OpenAI
import datetime
import random
import string
from metagpt.ext.stanford_town.memory.retrieve import new_agent_retrieve

BASE_URL = "https://api.chatanywhere.tech/v1"
API_KEY = "sk-zdCy8EUxdUzG772nUTAeSyqopVOFD2j68hwQi5MgEtPGpjMb"

def llm(prompt, max_tokens=1000):
    try:
        client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL
        )
        message = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=message,
            max_tokens=max_tokens
        )
        output = response.choices[0].message.content
        return output
    except Exception as e:
        print(e)
        return None

def get_embedding(text, model: str = "text-embedding-ada-002"):
    text = text.replace("\n", " ")
    embedding = None
    if not text:
        text = "this is blank"
    try:
        embedding = (
            OpenAI(api_key=API_KEY, base_url=BASE_URL).embeddings.create(input=[text], model=model).data[0].embedding
        )
    except Exception as e:
        print(e)
    if not embedding:
        raise ValueError("get_embedding failed")
    return embedding

def wake_up(role):
    prompt = f"""
    {role.scratch.get_str_iss()}
    In general, {role.scratch.get_str_lifestyle()}
    {role.scratch.get_str_firstname()}'s wake up hour:
    """
    prompt = prompt.strip()
    wake_up_hour = llm(prompt, max_tokens=5)
    try:
        wake_up_hour = wake_up_hour.strip().lower().split('am')[0]
    except:
        wake_up_hour = 8 # default wake_up_hour
    return wake_up_hour

def gen_daily_schedule(role, wake_up_hour):
    default_daily_schedule_list = [
        "wake up and complete the morning routine at 6:00 am",
        "eat breakfast at 7:00 am",
        "read a book from 8:00 am to 12:00 pm",
        "have lunch at 12:00 pm",
        "take a nap from 1:00 pm to 4:00 pm",
        "relax and watch TV from 7:00 pm to 8:00 pm",
        "go to bed at 11:00 pm"
    ]
    prompt = f"""
    {role.scratch.get_str_iss()}
    In general, {role.scratch.get_str_lifestyle()}
    Today is {role.scratch.get_str_curr_date_str()}. Here is {role.scratch.get_str_firstname()}'s plan today in broad-strokes (with the time of the day. e.g., have a lunch at 12:00 pm, watch TV from 7 to 8 pm): 1) wake up and complete the morning routine at {wake_up_hour}:00 am, 2)
    """
    prompt = prompt.strip()
    daily_schedule = llm(prompt, max_tokens=500)
    daily_schedule_list = []
    try:
        daily_schedule = daily_schedule.split(")")
        for i in daily_schedule:
            if i[-1].isdigit():
                i = i[:-1].strip()
                if i[-1] == "." or i[-1] == ",":
                    daily_schedule_list.append(i[:-1].strip())
    except:
        daily_schedule_list = default_daily_schedule_list
    daily_schedule_list = [f"wake up and complete the morning routine at {wake_up_hour}:00 am"] + daily_schedule_list
    return daily_schedule_list

def revise_identity(role):
    p_name = role.scratch.name
    focal_points = [
        f"{p_name}'s plan for {role.scratch.get_str_curr_date_str()}.",
        f"Important recent events for {p_name}'s life.",
    ]
    retrieved = new_agent_retrieve(role, focal_points)
    statements = "[Statements]\n"
    for key, val in retrieved.items():
        for i in val:
            statements += f"{i.created.strftime('%A %B %d -- %H:%M %p')}: {i.embedding_key}\n"
    plan_prompt = statements + "\n"
    plan_prompt += f"Given the statements above, is there anything that {p_name} should remember as they plan for"
    plan_prompt += f" *{role.scratch.curr_time.strftime('%A %B %d')}*? "
    plan_prompt += "If there is any scheduling information, be as specific as possible (include date, time, and location if stated in the statement)\n\n"
    plan_prompt += f"Write the response from {p_name}'s perspective."
    plan_note = llm(plan_prompt)

    thought_prompt = statements + "\n"
    thought_prompt += (
        f"Given the statements above, how might we summarize {p_name}'s feelings about their days up to now?\n\n"
    )
    thought_prompt += f"Write the response from {p_name}'s perspective."
    thought_note = llm(thought_prompt)

    currently_prompt = (
        f"{p_name}'s status from {(role.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}:\n"
    )
    currently_prompt += f"{role.scratch.currently}\n\n"
    currently_prompt += f"{p_name}'s thoughts at the end of {(role.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}:\n"
    currently_prompt += (plan_note + thought_note).replace("\n", "") + "\n\n"
    currently_prompt += f"It is now {role.scratch.curr_time.strftime('%A %B %d')}. Given the above, write {p_name}'s status for {role.scratch.curr_time.strftime('%A %B %d')} that reflects {p_name}'s thoughts at the end of {(role.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}. Write this in third-person talking about {p_name}."
    currently_prompt += "If there is any scheduling information, be as specific as possible (include date, time, and location if stated in the statement).\n\n"
    currently_prompt += "Follow this format below:\nStatus: <new status>"
    new_currently = llm(currently_prompt)

    role.scratch.currently = new_currently

    daily_req_prompt = role.scratch.get_str_iss() + "\n"
    daily_req_prompt += f"Today is {role.scratch.curr_time.strftime('%A %B %d')}. Here is {role.scratch.name}'s plan today in broad-strokes (with the time of the day. e.g., have a lunch at 12:00 pm, watch TV from 7 to 8 pm).\n\n"
    daily_req_prompt += f"Follow this format (the list should have 4~6 items but no more):\n"
    daily_req_prompt += f"1. wake up and complete the morning routine at <time>, 2. ..."

    new_daily_req = llm(daily_req_prompt)
    new_daily_req = new_daily_req.replace("\n", " ")
    role.scratch.daily_plan_req = new_daily_req

def gen_hourly_schedule(role, wake_up_hour):
    def _generate_schedule_for_given_hour(role, curr_hour_str, p_f_ds_hourly_org, hour_str, intermission2=None):
        def get_random_alphanumeric(i=6, j=6):
            """
            Returns a random alpha numeric strength that has the length of somewhere
            between i and j.

            args:
                i: min_range for the length
                j: max_range for the length
            returns:
                an alpha numeric str with the length of somewhere between i and j.
            """
            k = random.randint(i, j)
            x = "".join(random.choices(string.ascii_letters + string.digits, k=k))
            return x

        def create_prompt_input(persona, curr_hour_str, p_f_ds_hourly_org, hour_str, intermission2=None):
            schedule_format = ""
            for i in hour_str:
                schedule_format += f"[{persona.scratch.get_str_curr_date_str()} -- {i}]"
                schedule_format += "Activity: [Fill in]\n"
            schedule_format = schedule_format[:-1]

            intermission_str = "Here the originally intended hourly breakdown of"
            intermission_str += f" {persona.scratch.get_str_firstname()}'s schedule today: "
            for count, i in enumerate(persona.scratch.daily_req):
                intermission_str += f"{str(count + 1)}) {i}, "
            intermission_str = intermission_str[:-2]

            prior_schedule = ""
            if p_f_ds_hourly_org:
                prior_schedule = "\n"
                for count, i in enumerate(p_f_ds_hourly_org):
                    prior_schedule += f"[(ID:{get_random_alphanumeric()})"
                    prior_schedule += f" {persona.scratch.get_str_curr_date_str()} --"
                    prior_schedule += f" {hour_str[count]}] Activity:"
                    prior_schedule += f" {persona.scratch.get_str_firstname()}"
                    prior_schedule += f" is {i}\n"
            
            prompt_ending = f"[(ID:{get_random_alphanumeric()})"
            prompt_ending += f" {persona.scratch.get_str_curr_date_str()}"
            prompt_ending += f" -- {curr_hour_str}] Activity:"
            prompt_ending += f" {persona.scratch.get_str_firstname()} is"

            if intermission2:
                    intermission2 = f"\n{intermission2}"

            prompt_input = []
            prompt_input += [schedule_format]
            prompt_input += [persona.scratch.get_str_iss()]

            prompt_input += [prior_schedule + "\n"]
            prompt_input += [intermission_str]
            if intermission2:
                prompt_input += [intermission2]
            else:
                prompt_input += [""]
                prompt_input += [prompt_ending]

            return prompt_input
    
        prompt_input = create_prompt_input(role, curr_hour_str, p_f_ds_hourly_org, hour_str, intermission2)
        prompt = f"""
        Hourly schedule format: 
        {prompt_input[0]}
        ===
        {prompt_input[1]}
        {prompt_input[2]}
        {prompt_input[3]}{prompt_input[4]}
        {prompt_input[5]}
        """
        llm_output = llm(prompt, max_tokens=50)
        try:
            given_hour_schedule = llm_output.strip()
            if given_hour_schedule[-1] == ".":
                given_hour_schedule = given_hour_schedule[:-1]
            given_hour_schedule = given_hour_schedule.split("\n")[0]
            return given_hour_schedule
        except:
            return "asleep"
    hour_str = ["00:00 AM", "01:00 AM", "02:00 AM", "03:00 AM", "04:00 AM", "05:00 AM", "06:00 AM", "07:00 AM", "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM", "08:00 PM", "09:00 PM", "10:00 PM", "11:00 PM"]
    n_m1_activity = []
    diversity_repeat_count = 1
    for i in range(diversity_repeat_count):
        n_m1_activity_set = set(n_m1_activity)
        if len(n_m1_activity_set) < 5:
            n_m1_activity = []
            for count, curr_hour_str in enumerate(hour_str):
                if wake_up_hour > 0:
                    n_m1_activity += ["sleeping"]
                    wake_up_hour -= 1
                else:
                    n_m1_activity += [
                        _generate_schedule_for_given_hour(role, curr_hour_str, n_m1_activity, hour_str)
                    ]
    
    # Step 1
    _n_m1_hourly_compressed = []
    prev = None
    prev_count = 0
    for i in n_m1_activity:
        if i != prev:
            prev_count = 1
            _n_m1_hourly_compressed += [[i, prev_count]]
            prev = i
        elif _n_m1_hourly_compressed:
            _n_m1_hourly_compressed[-1][1] += 1
    
    # Step 2
    n_m1_hourly_compressed = []
    for task, duration in _n_m1_hourly_compressed:
        n_m1_hourly_compressed += [[task, duration * 60]]
    return n_m1_hourly_compressed

def long_term_planning(role, new_day):
    """
    Formulates the role's daily long-term plan if it is the start of a new
    day. This basically has two components: first, we create the wake-up hour,
    and second, we create the hourly schedule based on it.

    args:
        new_day: Indicates whether the current time signals a "First day",
                "New day", or False (for neither). This is important because we
                create the roles' long term planning on the new day.
    returns:
        pass
    """
    wake_up_hour = wake_up(role)
    wake_up_hour = int(wake_up_hour)
    
    if new_day == "First day":
        role.scratch.daily_req = gen_daily_schedule(role, wake_up_hour)
    elif new_day == "New day":
        revise_identity(role)
        daily_schedule_list = []
        daily_schedule = role.scratch.daily_plan_req.split(".")
        for i in daily_schedule:
            if len(i) > 5:
                if i[-1].isdigit():
                    i = i[:-1].strip()
                    if i[-1] == "." or i[-1] == ",":
                        i = i[:-1]
                daily_schedule_list.append(i.strip())
        role.scratch.daily_req = daily_schedule_list

    role.scratch.f_daily_schedule = gen_hourly_schedule(role, wake_up_hour)
    role.scratch.f_daily_schedule_hourly_org = role.scratch.f_daily_schedule[:]

    thought = f"This is {role.scratch.name}'s plan for {role.scratch.curr_time.strftime('%A %B %d')}:"
    for i in role.scratch.daily_req:
        thought += f" {i},"
    thought = thought[:-1] + "."
    created = role.scratch.curr_time
    expiration = role.scratch.curr_time + datetime.timedelta(days=30)
    s, p, o = (role.scratch.name, "plan", role.scratch.curr_time.strftime("%A %B %d"))
    keywords = set(["plan"])
    thought_poignancy = 5
    thought_embedding_pair = (thought, get_embedding(thought))
    role.a_mem.add_thought(
        created, expiration, s, p, o, thought, keywords, thought_poignancy, thought_embedding_pair, None
    )


async def startup():
    from metagpt.ext.stanford_town.roles.st_role import STRole
    from metagpt.ext.stanford_town.stanford_town import StanfordTown
    from metagpt.ext.stanford_town.utils.utils import copy_folder
    from metagpt.ext.stanford_town.utils.const import STORAGE_PATH
    from metagpt.ext.stanford_town.utils.mg_ga_transform import (
        get_reverie_meta,
        write_curr_sim_code,
        write_curr_step,
    )
    idea = "123"
    fork_sim_code = "base_the_ville_isabella_maria_klaus"
    sim_code = "stf_game_test"
    temp_storage_path = None
    investment = 30.0
    n_round = 500
    town = StanfordTown()
    copy_folder(str(STORAGE_PATH.joinpath(fork_sim_code)), str(STORAGE_PATH.joinpath(sim_code)))
    reverie_meta = get_reverie_meta(fork_sim_code)
    roles = []
    sim_path = STORAGE_PATH.joinpath(sim_code)
    sim_path.mkdir(exist_ok=True)
    for idx, role_name in enumerate(reverie_meta["persona_names"]):
        has_inner_voice = True if idx == 0 else False
        role = STRole(
            name=role_name,
            profile=role_name,
            sim_code=sim_code,
            step=reverie_meta.get("step", 0),
            start_time=reverie_meta.get("start_date"),
            curr_time=reverie_meta.get("curr_time"),
            sec_per_step=reverie_meta.get("sec_per_step"),
            has_inner_voice=has_inner_voice,
        )
        roles.append(role)
    write_curr_sim_code({"sim_code": sim_code}, temp_storage_path)
    write_curr_step({"step": reverie_meta.get("step", 0)}, temp_storage_path)
    await town.hire(roles)
    town.invest(investment)
    await roles[0].add_inner_voice('123')
    long_term_planning(roles[0], "First day")
    # long_term_planning(roles[0], "New day")

if __name__ == "__main__":
    import asyncio
    asyncio.run(startup())