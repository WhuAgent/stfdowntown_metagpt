# -*- coding:utf-8 -*-
"""
作者：86173
日期：2025年07月02日
"""
# home  = "the Ville:Isabella Rodriguez's apartment:main room"
# print(home.split(":"))
# if __name__ == "__main__":
#     index = ["action_location_sector_v1.txt", "action_location_object_vMar11.txt", "action_object_v2.txt", "generate_pronunciatio_v1.txt",
#              "generate_event_triple_v1.txt", "generate_obj_event_v1.txt", "generate_event_triple_v1.txt"]
#     prompt_path = "C:\\Users\\86173\\Desktop\\Agent-network\\Code\\new_stf\\stfdowntown_metagpt\\prompt.py"
#     for i in index:
#         i = "C:\\Users\\86173\\Desktop\\Agent-network\\Code\\new_stf\\stfdowntown_metagpt\\metagpt\\ext\\stanford_town\\prompts\\"+i
#         with open(i, "r", encoding="utf-8") as f:
#             with open(prompt_path, "a", encoding="utf-8") as f1:
#                 f1.write(i+'"""\n')
#                 f1.write(f.read())
#                 f1.write('"""\n\n')

from test1 import my_method

class agent:
    def chat_llm(self, prompt):
        print("agent chat_llm "+ prompt)
        return True

    def forward(self):
        my_method1 = my_method()
        return my_method1.generate_sector("some sectors", self)

if __name__ == "__main__":
    agent1 = agent()
    print(agent1.forward())