import numpy as np
from request import Request
from location import Location


class PDPTW:
    def __init__(self, name, requests, depot, vehicleCapacity):
        self.name = name
        self.requests = requests
        self.depot = depot

        # 🛡️ 导师终极安检锁：绝不允许 0 容量的“幽灵卡车”上路！
        if vehicleCapacity is None or int(vehicleCapacity) <= 0:
            self.capacity = 200
        else:
            self.capacity = int(vehicleCapacity)

        ##construct the set with all locations
        self.locations = set()
        self.locations.add(depot)
        for r in self.requests:
            self.locations.add(r.pickUpLoc)
            self.locations.add(r.deliveryLoc)

        # compute the distance matrix
        self.distMatrix = np.zeros((len(self.locations), len(self.locations)))  # init as nxn matrix
        for i in self.locations:
            for j in self.locations:
                distItoJ = Location.getDistance(i, j)
                self.distMatrix[i.nodeID, j.nodeID] = distItoJ

    def print(self):
        print(" PDPTW problem " + self.name + " with " + str(
            len(self.requests)) + " requests and a vehicle capacity of " + str(self.capacity))

    @staticmethod
    def readInstance(fileName):
        """
        自适应智能双模解析器
        完全抛弃死板的字符串匹配，通过数据列特征自动识别格式，完美兼容官网56个标准算例
        """
        with open(fileName, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # ----------------- 尝试模式 B：标准 SINTEF / Li & Lim 纯数字格式 -----------------
        customer_lines = []
        capacity = 200  # 默认给个保底容量值

        # 1. 智能寻找车辆容量 CAPACITY
        for i, line in enumerate(lines):
            if "CAPACITY" in line.upper():
                parts = line.split()
                if len(parts) >= 2 and parts[0].upper() == "CAPACITY":
                    try:
                        capacity = int(float(parts[1]))
                    except:
                        pass
                elif len(parts) >= 2 and "CAPACITY" in parts[1].upper():
                    try:
                        # 🔧 修复：必须用 [-1] 抓取最后一个数据（载重），绝对不能用 [0]
                        capacity = int(float(lines[i + 1].split()[-1]))
                    except:
                        pass
                else:
                    if i + 1 < len(lines):
                        next_parts = lines[i + 1].split()
                        if next_parts:
                            try:
                                capacity = int(float(next_parts[-1]))
                            except:
                                pass
                break

        # 2. 核心特征抓取：提取所有符合【首列为整数且总列数>=7】的标准核心数据行
        for line in lines:
            parts = line.split()
            if len(parts) >= 7:
                try:
                    int(float(parts[0]))  # 检查第一列是否代表一个整数ID
                    customer_lines.append(parts)
                except ValueError:
                    continue

        # 3. 验证是否成功抓取到标准格式的数据（第一个节点必须是大本营0）
        has_depot_0 = False
        if customer_lines:
            try:
                if int(float(customer_lines[0][0])) == 0:
                    has_depot_0 = True
            except:
                pass

        if has_depot_0:
            # ======= 确认进入：模式 B（标准官网格式）=======
            raw_nodes = {}
            for parts in customer_lines:
                try:
                    c_id = int(float(parts[0]))
                    raw_nodes[c_id] = {
                        'x': int(float(parts[1])), 'y': int(float(parts[2])),
                        'demand': int(float(parts[3])), 'ready': int(float(parts[4])),
                        'due': int(float(parts[5])), 'service': int(float(parts[6])),
                        'p_no': int(float(parts[7])), 'd_no': int(float(parts[8]))
                    }
                except:
                    continue

            if 0 in raw_nodes:
                dep_d = raw_nodes[0]
                depot = Location(0, dep_d['x'], dep_d['y'], 0, dep_d['ready'], dep_d['due'], dep_d['service'], 0, 0, 0)

                requests = []
                nodeCount = 1
                pairs = {}

                # 找出所有的取货点
                for c_id, node in raw_nodes.items():
                    if c_id == 0: continue
                    if node['p_no'] == 0 and node['d_no'] > 0:
                        pairs[c_id] = node['d_no']

                requestCount = 1
                for p_id, d_id in pairs.items():
                    if p_id in raw_nodes and d_id in raw_nodes:
                        p_n = raw_nodes[p_id]
                        d_n = raw_nodes[d_id]

                        p_loc = Location(requestCount, p_n['x'], p_n['y'], p_n['demand'], p_n['ready'], p_n['due'],
                                         p_n['service'], 0, 1, nodeCount)
                        nodeCount += 1

                        d_loc = Location(requestCount, d_n['x'], d_n['y'], d_n['demand'], d_n['ready'], d_n['due'],
                                         d_n['service'], 0, -1, nodeCount)
                        nodeCount += 1

                        req = Request(p_loc, d_loc, requestCount)
                        requests.append(req)
                        requestCount += 1

                return PDPTW(fileName, requests, depot, capacity)

        # ----------------- 降级进入 模式 A：GitHub 原作者特有自制格式 -----------------
        servStartTime = 0
        requests = list()
        unmatchedPickups = dict()
        unmatchedDeliveries = dict()
        nodeCount = 0
        requestCount = 1

        capacity = 200
        for line in reversed(lines):
            if line.strip() and not line.strip().isalpha():
                parts = line.split()
                if len(parts) >= 1:
                    try:
                        capacity = int(parts[-1])
                        break
                    except:
                        pass

        for line in lines:
            asList = []
            n = 13
            for index in range(0, len(line), n):
                asList.append(line[index: index + n].strip())

            if not asList or not asList[0]:
                continue
            lID = asList[0]

            if lID.startswith("D") or lID.startswith("C"):
                try:
                    x = int(float(asList[2]))
                    y = int(float(asList[3]))
                except:
                    continue

                if lID.startswith("D"):
                    depot = Location(0, x, y, 0, 0, 0, 0, servStartTime, 0, nodeCount)
                    nodeCount += 1
                elif lID.startswith("C"):
                    try:
                        lType = asList[1]
                        demand = int(float(asList[4]))
                        startTW = int(float(asList[5]))
                        endTW = int(float(asList[6]))
                        servTime = int(float(asList[7]))
                        partnerID = asList[8]
                    except:
                        continue

                    if lType == "cp":
                        if partnerID in unmatchedDeliveries:
                            deliv = unmatchedDeliveries.pop(partnerID)
                            pickup = Location(deliv.requestID, x, y, demand, startTW, endTW, servTime, servStartTime, 1,
                                              nodeCount)
                            nodeCount += 1
                            req = Request(pickup, deliv, deliv.requestID)
                            requests.append(req)
                        else:
                            pickup = Location(requestCount, x, y, demand, startTW, endTW, servTime, servStartTime, 1,
                                              nodeCount)
                            nodeCount += 1
                            requestCount += 1
                            unmatchedPickups[lID] = pickup
                    elif lType == "cd":
                        if partnerID in unmatchedPickups:
                            pickup = unmatchedPickups.pop(partnerID)
                            deliv = Location(pickup.requestID, x, y, demand, startTW, endTW, servTime, servStartTime,
                                             -1, nodeCount)
                            nodeCount += 1
                            req = Request(pickup, deliv, pickup.requestID)
                            requests.append(req)
                        else:
                            deliv = Location(requestCount, x, y, demand, startTW, endTW, servTime, servStartTime, -1,
                                             nodeCount)
                            nodeCount += 1
                            requestCount += 1
                            unmatchedDeliveries[lID] = deliv

        return PDPTW(fileName, requests, depot, capacity)