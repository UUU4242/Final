import sys
from route import Route

class Repair:
    '''
    Class that represents repair methods

    Parameters
    ----------
    problem : PDPTW
        The problem instance that we want to solve.
    currentSolution : Solution
        The current solution in the ALNS algorithm
    randomGen : Random
        random number generator

    '''

    def __init__(self, problem, solution):
        self.problem = problem
        self.solution = solution

    def computeDiff(self, preNode, afterNode, insertNode):
        '''
        Method that calculates the cost of inserting a new node
        Parameters
        ----------
        preNode: Location
        afterNode: Location
        insertNode: Location
        '''

        return self.problem.distMatrix[preNode.nodeID][insertNode.nodeID] + self.problem.distMatrix[afterNode.nodeID][
            insertNode.nodeID] - self.problem.distMatrix[preNode.nodeID][afterNode.nodeID]

    def findRegretInsertion(self):
        '''
        Method that finds the insertion to maximize regret value
        Returns
        -------
        [request, route, prevNode_index, afterNode_index]
        '''

        maxRegret = -1
        insertRoute = None
        insertRequest = None
        preNode_index = -1
        afterNode_index = -1
        maxCost = sys.maxsize  # extremely large number
        for request in self.solution.notServed:
            tempCost = []
            inserted = False
            # print('new request----------')
            # print(request)
            for route in self.solution.routes:
                requestsCopy = route.requests.copy()
                requestsCopy.add(request)
                for i in range(1, len(route.locations)):
                    for j in range(i + 1, len(route.locations) + 1):  # delivery after pickup
                        locationsCopy = route.locations.copy()
                        cost = route.compute_cost_add_one_request(i, j, request)
                        locationsCopy.insert(i, request.pickUpLoc)
                        locationsCopy.insert(j, request.deliveryLoc)  # depot at the end
                        afterInsertion = Route(locationsCopy, requestsCopy, self.problem)
                        if afterInsertion == None:
                            continue
                        # check if insertion is feasible
                        if afterInsertion.feasible:
                            inserted = True
                            tempCost.append([cost, route, i, j])

            # if we have only one feasible insertion
            if len(tempCost) == 1:
                locList = [self.problem.depot, request.pickUpLoc, request.deliveryLoc, self.problem.depot]
                newRoute = Route(locList, {request}, self.problem)
                diff = newRoute.distance
                tempCost.append([diff, None, 0, 0])

            # if we were not able to insert, create a new route
            if not inserted:
                # print('not insert')
                # create a new route with the request
                locList = [self.problem.depot, request.pickUpLoc, request.deliveryLoc, self.problem.depot]
                newRoute = Route(locList, {request}, self.problem)
                diff = newRoute.distance
                tempCost.append([diff, None, 0, 0])

            tempCost = sorted(tempCost, key = lambda d: d[0], reverse = False)
            # print('sorted tempCost')
            # print(tempCost)

            if len(tempCost) > 1 and (tempCost[1][0] - tempCost[0][0]) > maxRegret:
                maxRegret = tempCost[1][0] - tempCost[0][0]
                # print('maxRegret',maxRegret)
                insertRoute = tempCost[0][1]
                insertRequest = request
                preNode_index = tempCost[0][2]
                afterNode_index = tempCost[0][3]
            # all request can only be inserted into a new route, choose greedy insertion to minimize the cost
            # 】：加入 (insertRequest is None) 兜底判定，防止因为全都不符合条件而返回 None
            elif len(tempCost) == 1 and (maxRegret <= 0) and (insertRequest is None or tempCost[0][0] < maxCost):
                maxRegret = 0
                maxCost = tempCost[0][0]
                insertRoute = tempCost[0][1]
                insertRequest = request
                preNode_index = tempCost[0][2]
                afterNode_index = tempCost[0][3]

            # 【终极保险】：如果遇到极端变态算例，实在选不出来，强行抓取第一个未分配订单兜底
        if insertRequest is None:
            insertRequest = self.solution.notServed[0]
            insertRoute = None
            preNode_index = 0
            afterNode_index = 0

        return insertRequest, insertRoute, preNode_index, afterNode_index
    # @Log('time_output.csv')
    def executeRegretInsertion(self):
        """
        Method that inserts the unserved request with the largest regret first in the solution

        This is repair method number 2 in the ALNS

        """
        while len(self.solution.notServed) > 0:
            insertRequest, insertRoute, preNode_index, afterNode_index = self.findRegretInsertion()
            # print(insertRequest, insertRoute, preNode_index, afterNode_index)
            self.solution.addRequest(insertRequest, insertRoute, preNode_index, afterNode_index)

            # for route in self.solution.routes:
            #     route.print()

    # @Log('time_output.csv')
    def executeGreedyInsertion(self):
        # 1. 核心改进：按“时间窗紧急程度”从严到松排序（不仅看宽度，看DueDate）
        self.solution.notServed.sort(key=lambda req: req.pickUpLoc.endTW)

        for req in self.solution.notServed.copy():
            best_route = None
            best_cost = sys.maxsize
            best_afterInsertion = None
            best_pos = None

            # 2. 扫描所有车的所有位置，寻找【全局最小增量】
            for route in self.solution.routes:
                # 遍历插入位置
                for i in range(1, len(route.locations)):
                    for j in range(i + 1, len(route.locations) + 1):
                        locationsCopy = route.locations.copy()
                        locationsCopy.insert(i, req.pickUpLoc)
                        locationsCopy.insert(j, req.deliveryLoc)
                        afterInsertion = Route(locationsCopy, route.requests | {req}, self.problem)

                        if afterInsertion.feasible:
                            cost = afterInsertion.computeDistance() - route.distance
                            if cost < best_cost:
                                best_cost = cost
                                best_route = route
                                best_afterInsertion = afterInsertion

            # 3. 执行插入
            if best_route is not None:
                self.solution.routes.remove(best_route)
                self.solution.routes.append(best_afterInsertion)
                self.solution.served.append(req)
                self.solution.notServed.remove(req)
            else:
                # 只有全网都装不下时，才开新车
                locList = [self.problem.depot, req.pickUpLoc, req.deliveryLoc, self.problem.depot]
                newRoute = Route(locList, {req}, self.problem)
                self.solution.routes.append(newRoute)
                self.solution.served.append(req)
                self.solution.notServed.remove(req)

    # @Log('time_output.csv')
    def executeRandomInsertion(self, randomGen):
        """
        Method that randomly inserts the unserved requests in the solution

        This is repair method number 0 in the ALNS

        Parameters
        ----------
        randomGen : Random
            Used to generate random numbers

        """

        # iterate over the list with unserved requests
        while len(self.solution.notServed) > 0:
            # pick a random request
            req = randomGen.choice(self.solution.notServed)

            # keep track of routes in which req could be inserted
            potentialRoutes = self.solution.routes.copy()
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
                    self.solution.routes.remove(randomRoute)
                    self.solution.routes.append(afterInsertion)
                    self.solution.distance += cost
                    break

            # if we were not able to insert, create a new route
            if not inserted:
                # create a new route with the request
                locList = [self.problem.depot, req.pickUpLoc, req.deliveryLoc, self.problem.depot]
                newRoute = Route(locList, {req}, self.problem)
                self.solution.routes.append(newRoute)
                self.solution.distance += newRoute.distance
            # update the lists with served and notServed requests
            self.solution.served.append(req)
            self.solution.notServed.remove(req)

