from route import Route

class Solution:
    """
    Method that represents a solution to the PDPTW

    Attributes
    ----------
    problem : PDPTW
        the problem that corresponds to this solution
    routes : List of Routes
         Routes in the current solution
    served : List of Requests
        Requests served in the current solution
    notServed : List of Requests
         Requests not served in the current solution 
    distance : int
        total distance of the current solution
    """

    def __init__(self, problem, routes, served, notServed):
        self.problem = problem
        self.routes = routes
        self.served = served
        self.notServed = notServed
        self.distance = self.computeDistance()

    def computeDistance(self):
        """
        Method that computes the distance of the solution
        """
        self.distance = 0
        for route in self.routes:
            self.distance += route.distance

        vehicle_fixed_cost = 500
        self.distance += len(self.routes) * vehicle_fixed_cost

        return self.distance


    def computeDistanceWithNoise(self, max_arc_dist, noise, randomGen):
        """
        纠编版：去除了内部会被高频刷新的错误计数器。
        直接根据全局指挥官决定的真实 noise 值进行加噪。
        """
        if noise > 0:
            # 运筹学经典加噪公式：在原有真实总距离基础上，叠加一个基于最大边长的随机扰动
            random_noise = randomGen.uniform(-noise, noise) * max_arc_dist
            self.distance += random_noise

    # 如果全局传入的 noise 是 0，则说明本轮不加噪，保持真实的 distance 成绩不变

    def calculateMaxArc(self):
        max_arc_length = 0
        for route in self.routes:
            for i in range(1, len(route.locations)):
                first_node_ID = route.locations[i - 1].nodeID
                second_node_ID = route.locations[i].nodeID
                arc_length = self.problem.distMatrix[first_node_ID][second_node_ID]
                if arc_length > max_arc_length:
                    max_arc_length = arc_length
        return max_arc_length

    def print(self):
        """
        Method that prints the solution
        """
        nRoutes = len(self.routes)
        nNotServed = len(self.notServed)

        # 🌟 优化：剥离所有惩罚成本，计算纯粹的物理行驶距离
        real_distance = sum(r.computeDistance() for r in self.routes)

        print(f"【系统评估总成本】: {self.distance}")
        print(f"【真正行驶里程】: {real_distance}")
        print(f"【车辆数】: {nRoutes} 辆")
        print(f"【未服务订单】: {nNotServed} 个")
        print("详细路线: ")

        for route in self.routes:
            route.print()

        print("\n\n")

    def executeRandomRemoval(self, nRemove, randomGen):
        """
        Method that executes a random removal of requests
        
        This is destroy method number 1 in the ALNS

        Parameters
        ----------
        nRemove : int
            number of requests that is removed.
                 
        Parameters
        ----------
        randomGen : Random
            Used to generate random numbers

        """
        print('nRemove = ' + str(nRemove))
        for i in range(nRemove):
            # terminate if no more requests are served
            if len(self.served) == 0:
                break
            # pick a random request and remove it from the solutoin
            req = randomGen.choice(self.served)
            self.removeRequest(req)

        self.distance = self.computeDistance()

    def removeRequest(self, request):
        """
        Method that removes a request from the solution
        """
        # 1. 从路线和车辆中移除该订单
        for route in self.routes:
            if request in route.requests:
                route.locations.remove(request.pickUpLoc)
                route.locations.remove(request.deliveryLoc)
                route.requests.remove(request)

                # 🌟 降车核心：如果这辆车被清空了，立刻强制从车队中裁撤注销！
                if len(route.requests) == 0:
                    self.routes.remove(route)
                else:
                    route.distance = route.computeDistance()
                break  # 已经在路线中找到了，跳出 for 循环

        # 2. 更新全局订单状态列表（🛡️ 加上防崩溃锁）
        if request in self.served:
            self.served.remove(request)

        if request not in self.notServed:
            self.notServed.append(request)

    def addRequest(self, request, insertRoute, prevNode_index, afterNode_index):
        '''
        Method that add a request to the solution
        '''
        if insertRoute == None:
            locList = [self.problem.depot, request.pickUpLoc, request.deliveryLoc, self.problem.depot]
            newRoute = Route(locList, {request}, self.problem)
            self.routes.append(newRoute)
            self.distance += newRoute.distance
        else:
            for route in self.routes:
                if route == insertRoute:
                    res = route.addRequest(request, prevNode_index, afterNode_index)
                    if res == -1:
                        locList = [self.problem.depot, request.pickUpLoc, request.deliveryLoc, self.problem.depot]
                        newRoute = Route(locList, {request}, self.problem)
                        self.routes.append(newRoute)
                        self.distance += newRoute.distance
                    else:
                        self.distance += res
        # update lists with served and unserved requests
        self.served.append(request)
        self.notServed.remove(request)
        # update distance
        # self.computeDistance()

    def copy(self):
        """
        Method that creates a copy of the solution and returns it
        """
        # need a deep copy of routes because routes are modifiable
        routesCopy = list()
        for route in self.routes:
            routesCopy.append(route.copy())
        copy = Solution(self.problem, routesCopy, self.served.copy(), self.notServed.copy())
        copy.computeDistance()
        return copy

    def executeRandomInsertion(self, randomGen):
        """
        Method that randomly inserts the unserved requests in the solution
        
        This is repair method number 1 in the ALNS
        
        Parameters
        ----------
        randomGen : Random
            Used to generate random numbers

        """
        # iterate over the list with unserved requests
        while len(self.notServed) > 0:
            # pick a random request
            req = randomGen.choice(self.notServed)

            # keep track of routes in which req could be inserted
            potentialRoutes = self.routes.copy()
            inserted = False
            while len(potentialRoutes) > 0:
                # pick a random route
                randomRoute = randomGen.choice(potentialRoutes)

                afterInsertion, cost = randomRoute.greedyInsert(req)
                if afterInsertion == None:
                    # insertion not feasible, remove route from potential routes
                    potentialRoutes.remove(randomRoute)
                else:
                    # insertion feasible, update routes and break from while loop
                    inserted = True
                    # print("Possible")
                    self.routes.remove(randomRoute)
                    self.routes.append(afterInsertion)
                    self.distance += cost
                    break

            # if we were not able to insert, create a new route
            if not inserted:
                # create a new route with the request
                locList = [self.problem.depot, req.pickUpLoc, req.deliveryLoc, self.problem.depot]
                newRoute = Route(locList, {req}, self.problem)
                self.routes.append(newRoute)
                self.distance += newRoute.distance
            # update the lists with served and notServed requests
            self.served.append(req)
            self.notServed.remove(req)
        # self.computeDistance()
