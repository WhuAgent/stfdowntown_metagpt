# 和大模型交互的提示词写在这里
action_location_sector = """
Variables:
!<INPUT 0>! -- Persona name
!<INPUT 1>! -- Persona living sector (从 living_area 提取)
!<INPUT 2>! -- Living sector arenas (居住区子区域)
!<INPUT 3>! -- Persona name (重复二)
!<INPUT 4>! -- Persona current sector
!<INPUT 5>! -- Current sector arenas (当前区子区域)
!<INPUT 6>! -- Daily plan requirement (带换行符或空)
!<INPUT 7>! -- Accessible sectors (过滤后的可访问区域)
!<INPUT 8>! -- Persona name (重复三)
!<INPUT 9>! -- Action description part 1 (括号前内容)
!<INPUT 10>! -- Action description part 2 (括号内内容)
!<INPUT 11>! -- Persona name (重复四)
<commentblockmarker>###</commentblockmarker>
Task -- choose an appropriate area  from the area options for a task at hand. 

Sam Kim lives in {Sam Kim's house} that has Sam Kim's room, bathroom, kitchen.
Sam Kim is currently in {Sam Kim's house} that has Sam Kim's room, bathroom, kitchen. 
Area options: {Sam Kim's house, The Rose and Crown Pub, Hobbs Cafe, Oak Hill College, Johnson Park, Harvey Oak Supply Store, The Willows Market and Pharmacy}.
* Stay in the current area if the activity can be done there. Only go out if the activity needs to take place in another place.
* Must be one of the "Area options," verbatim.
For taking a walk, Sam Kim should go to the following area: {Johnson Park}
---
Jane Anderson lives in {Oak Hill College Student Dormatory} that has Jane Anderson's room.
Jane Anderson is currently in {Oak Hill College} that has a classroom, library
Area options: {Oak Hill College Student Dormatory, The Rose and Crown Pub, Hobbs Cafe, Oak Hill College, Johnson Park, Harvey Oak Supply Store, The Willows Market and Pharmacy}. 
* Stay in the current area if the activity can be done there. Only go out if the activity needs to take place in another place.
* Must be one of the "Area options," verbatim.
For eating dinner, Jane Anderson should go to the following area: {Hobbs Cafe}
---
!<INPUT 0>! lives in {!<INPUT 1>!} that has !<INPUT 2>!.
!<INPUT 3>! is currently in {!<INPUT 4>!} that has !<INPUT 5>!. !<INPUT 6>!
Area options: {!<INPUT 7>!}. 
* Stay in the current area if the activity can be done there. Only go out if the activity needs to take place in another place.
* Must be one of the "Area options," verbatim.
!<INPUT 8>! is !<INPUT 9>!. For !<INPUT 10>!, !<INPUT 11>! should go to the following area: {"""

action_location_arena = """
Variables: 
!<INPUT 0>! -- Persona name
!<INPUT 1>! -- Target sector
!<INPUT 2>! -- Target sector's all arenas
!<INPUT 3>! -- Persona name
!<INPUT 4>! -- Action description1
!<INPUT 5>! -- Action description2
!<INPUT 6>! -- Persona name
!<INPUT 7>! -- Target sector
!<INPUT 8>! -- Target sector's all arenas

<commentblockmarker>###</commentblockmarker>
Jane Anderson is in kitchen in Jane Anderson's house.
Jane Anderson is going to Jane Anderson's house that has the following areas: {kitchen,  bedroom, bathroom}
Stay in the current area if the activity can be done there. Never go into other people's rooms unless necessary.
For cooking, Jane Anderson should go to the following area in Jane Anderson's house:
Answer: {kitchen}
---
Tom Watson is in common room in Tom Watson's apartment. 
Tom Watson is going to Hobbs Cafe that has the following areas: {cafe}
Stay in the current area if the activity can be done there. Never go into other people's rooms unless necessary.
For getting coffee, Tom Watson should go to the following area in Hobbs Cafe:
Answer: {cafe}
---

!<INPUT 0>! is going to !<INPUT 1>! that has the following areas: {!<INPUT 2>!}
* Stay in the current area if the activity can be done there. 
* NEVER go into other people's rooms unless necessary.
!<INPUT 3>! is !<INPUT 4>!. For !<INPUT 5>!, !<INPUT 6>! should go to the following area in !<INPUT 7>! (MUST pick one of {!<INPUT 8>!}):
Answer: {"""

action_location_object = """
Variables: 
!<INPUT 0>! -- curr action seq
!<INPUT 1>! -- Objects available

<commentblockmarker>###</commentblockmarker>
Current activity: sleep in bed
Objects available: {bed, easel, closet, painting}
Pick ONE most relevant object from the objects available: bed
---
Current activity: painting
Objects available: {easel, closet, sink, microwave}
Pick ONE most relevant object from the objects available: easel
---
Current activity: cooking
Objects available: {stove, sink, fridge, counter}
Pick ONE most relevant object from the objects available: stove
---
Current activity: watch TV
Objects available: {couch, TV, remote, coffee table}
Pick ONE most relevant object from the objects available: TV
---
Current activity: study
Objects available: {desk, computer, chair, bookshelf}
Pick ONE most relevant object from the objects available: desk
---
Current activity: talk on the phone
Objects available: {phone, charger, bed, nightstand}
Pick ONE most relevant object from the objects available: phone
---
Current activity: !<INPUT 0>!
Objects available: {!<INPUT 1>!}
Pick ONE most relevant object from the objects available:"""

action_pronunciatio = """
generate_pronunciatio_v1.txt

Variables: 
!<INPUT 0>! -- Action description

<commentblockmarker>###</commentblockmarker>
Convert an action description to an emoji (important: use two or less emojis).
example_output:🛁🧖‍
The value for the output must ONLY contain the emojis.
Action description: !<INPUT 0>!
Emoji:"""

action_triple = """
generate_event_triple_v1.txt

Variables: 
!<INPUT 0>! -- Persona's full name. 
!<INPUT 1>! -- Current action description
!<INPUT 2>! -- Persona's full name. 

<commentblockmarker>###</commentblockmarker>
Task: Turn the input into (subject, predicate, object) or (subject, is, doing something/being done).
Input: Sam Johnson is eating breakfast. 
Output: (Dolores Murphy, eat, breakfast)
---
Input: Merrie Morris is running on a treadmill. 
Output: (Merrie Morris, run, treadmill)
---
Input: The bed is being slept in.
Output: (bed , is , slept in)
---
Input: Jane Cook is sleeping.
Output: (Jane Cook, is, sleeping)
## Please follow the examples above to give out left two elements, strictly in form of (subject, predicate, object) not empty any element!!!
Input: !<INPUT 0>! is !<INPUT 1>!. 
Output: (!<INPUT 2>!,
"""

obj_desp = """
generate_obj_event_v1.txt

Variables: 
!<INPUT 0>! -- Object name 
!<INPUT 1>! -- Persona name
!<INPUT 2>! -- Persona action event description 
!<INPUT 3>! -- Object name 
!<INPUT 4>! -- Object name 

<commentblockmarker>###</commentblockmarker>
Task: We want to understand the state of an object that is being used by someone. 

Let's think step by step. 
We want to know about !<INPUT 0>!'s state.
For example:
bed is being slept in.
table is being used.
refrigerator is open.
Step 1. !<INPUT 1>! is at/using the !<INPUT 2>!.
Step 2. Describe the !<INPUT 3>!'s state: !<INPUT 4>! is"""

obj_triple = """
generate_event_triple_v1.txt

Variables: 
!<INPUT 0>! -- Persona's full name. 
!<INPUT 1>! -- Current action description
!<INPUT 2>! -- Persona's full name. 

<commentblockmarker>###</commentblockmarker>
Task: Turn the input into (subject, predicate, object) or (subject, is, doing something/being done).
Input: Sam Johnson is eating breakfast. 
Output: (Dolores Murphy, eat, breakfast)
---
Input: Merrie Morris is running on a treadmill. 
Output: (Merrie Morris, run, treadmill)
---
Input: The bed is being slept in.
Output: (bed , is , slept in)
---
Input: Jane Cook is sleeping.
Output: (Jane Cook, is, sleeping)
## Please follow the examples above to give out left two elements, strictly in form of (subject, predicate, object) not empty any element!!!
Input: !<INPUT 0>! is !<INPUT 1>!. 
Output: (!<INPUT 2>!,
"""

