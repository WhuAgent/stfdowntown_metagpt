# -*- coding:utf-8 -*-
"""
作者：86173
日期：2025年07月11日
"""

class my_method:
    def generate_prompt(self, prompt):
        return prompt+" generate"

    def generate_sector(self, info, agent_instance):
        prompt = self.generate_prompt(info)
        return agent_instance.chat_llm(prompt)
