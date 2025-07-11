from agent_network.base import BaseAgent

from memory import MemoryTree, AgentMemory, Scratch

from gen_action_details import GenActionDetails

class Environment(BaseAgent):
    def __init__(self, network, config, logger):
        super().__init__(network, config, logger)
    
    
    def generate_talk(self):
        pass
    
    def update_agent_status(self):
        pass
    
    def generate_observe_events(self):
        pass
        
    def forward(self, messages, **kwargs):
        # TODO: 从上下文中获取相关信息更新记忆
        spatial_memory = MemoryTree()
        associative_memory = AgentMemory()
        scratch_memory = Scratch()
        
        # 需要的记忆从上面三个变量里面去取，需要 Agent 的动作则从 kwargs 中取。
        self.generate_talk()
        
        self.update_agent_status()
        
        self.generate_observe_events()
        
        results = {
            
        }
        
        return results
    
    
class Persona(BaseAgent):
    def __init__(self, network, config, logger):
        super().__init__(network, config, logger)
        
    def retreive(self):
        pass
    
    def reflection_after_talk(self):
        pass
    
    def plan(self):
        pass
    
    def reflection(self):
        pass
        
    def forward(self, messages, **kwargs):
        # TODO: 从上下文中获取相关信息更新记忆
        spatial_memory = MemoryTree()
        associative_memory = AgentMemory()
        scratch_memory = Scratch()


        # 接下来的部分应该放在plan函数里面
        # ===================================================>
        # gen_action_details根据一句计划描述生成相应的具体动作信息
        # plan的前置阶段会分解小时计划，生成动作描述与持续时间
        act_desp = "sleeping"
        act_dura = "120"
        # 还需要observe的函数实现
        access_tile = None
        # access_tile = role.rc.env.observe(
        #     obs_params=EnvObsParams(obs_type=EnvObsType.GET_TITLE, coord=role.scratch.curr_tile)
        # )
        GenActionDetails().run(scratch_memory, spatial_memory, act_desp, act_dura, access_tile)
        # <======================================================
        
        # 需要的记忆从上面三个变量里面去取，需要环境返回的从 kwargs 中取。
        self.retreive()
        self.reflection_after_talk()
        self.plan()
        self.reflection()
        
        # TODO：记忆更新并回写上下文
        
        results = {}
        return results 
