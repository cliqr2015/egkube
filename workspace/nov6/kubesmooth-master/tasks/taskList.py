
class taskList:
    """Class constant values """
    taskdata = {}
    tasknum = 4
    task1 = "kubectl create sa prod-mgmt-tiller-account"
    task2 = "helm init --tiller-namespace default"
    task3 = "helm init --service-account  tiller --tiller-namespace default --upgrade"
    task4 = "kubectl create secret docker-registry suite-image-pull-secret --docker-username=multicloudsuite.gen --docker-password=AKCp5aTvLmuvA2d1eRkiehsSAySuWZiyEv76bczZWzHe7bq5W96drHsmUzKus6v2ZsYXqMFje --docker-email=suite@cisco.com --docker-server=devhub-docker.cisco.com"


    def __init__(self):
        self.taskdata["Task1"] = self.task1
        self.taskdata["Task2"] = self.task3
        self.taskdata["Task3"] = self.task3
        self.taskdata["Task4"] = self.task4


if __name__ == "__main__":
    print "Class for tasks/cmds"


