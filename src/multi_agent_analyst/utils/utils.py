import uuid

class ObjectStore:
    def __init__(self):
        self.store = {}
    
    def save(self, obj):
        obj_id = f"obj_{uuid.uuid4().hex[:8]}"
        self.store[obj_id] = obj
        #could potentially save the results of all intermediate steps inside a STEP (S1, ...)
        return obj_id

    def get(self, obj_id):
        return self.store[obj_id]


object_store = ObjectStore()


class CurrentToolContext:
    def __init__(self):
        self.dict={'DataAgent':{}, 'AnalysisAgent':{}, 'VisualizationAgent':{}}

    def set(self,agent, step, data):
        self.dict[agent][step]=data
    
    def get(self,agent, step_id):
        return self.dict[agent][step_id]
    


context=CurrentToolContext()
