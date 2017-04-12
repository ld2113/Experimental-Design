#from CandPythonParser import CandPythonParser
#from CUDAParser import CUDAParser
from ParsedModel_SDE import ParsedModel

class Writer:
    def __init__(self, modelName = "", inputPath = "", outputPath = ""):
        self.parsedModel = ParsedModel()
        
        if(modelName == ""):
            self.parsedModel.name = "unnamedModel"
        else:
            self.parsedModel.name = modelName
