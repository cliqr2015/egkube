
class taskList:
    """Class constant values """
    taskdata = {}
    tasknum = 1
    task1 = "helm install --name c3-framework --set global.namespace=cisco,global.suiteMonitoring=false,global.suiteLogging=false https://repo.ci.ciscolabs.com/CPSG_scarletwitch/charts/postmerge/common-framework-0.0.14408.tgz"


    def __init__(self):
        self.taskdata["Task1"] = self.task1



if __name__ == "__main__":
    print "Class for tasks/cmds"


