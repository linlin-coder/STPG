from enum import Enum,unique

class Digraph:
    """
    define stardand graph
    """
    def __init__(self, num):
        self.num_vertices = num
        self.num_edges = 0
        self.adj_list = [[] for _ in range(num)]

    def count_vertices(self):
        return self.num_vertices

    def count_edges(self):
        return self.num_edges

    def point_edge(self, x, y):
        """
        add an adge of vertex x: x --> y
        :param x: node start
        :param y: node end
        :return: None
        """
        self.adj_list[x].append(y)

    def point_to_vertices(self, x):
        return self.adj_list[x]

    def reverse_digraph(self):
        rvs_digraph = Digraph(self.num_vertices)
        for index, queue in enumerate(self.adj_list):
            for v in queue:
                rvs_digraph.point_edge(v, index)
        return rvs_digraph

def TestDigraph():
    graph = Digraph(5)

    graph.point_edge(3, 0)
    graph.point_edge(0, 2)

    reverse_graph = graph.reverse_digraph()
    print(reverse_graph)

# @unique
class ColorTask(Enum):
    white = "w"     # 表示图中未探索顶点
    black = "b"     # 表示图中正在探索顶点
    bary = "g"      # 表示图中已探索顶点

class Vertext():  # 包含了顶点信息,以及顶点连接边
    """
    reference:https://blog.csdn.net/jqsfjqsf/article/details/113793850
    """
    def __init__(self, key):            # key表示是添加的顶点
        self.id = key
        self.connectedTo = {}           # 初始化临接列表

    def addNeighbor(self, nbr, weight=0):  # 这个是赋值权重的函数
        self.connectedTo[nbr] = weight

    def __str__(self):
        return str(self.id) + ' connectedTo: ' + str([x.id for x in self.connectedTo])

    def getConnections(self):  # 得到这个顶点所连接的其他的所有的顶点 (keys类型是class)
        return self.connectedTo.keys()

    def getId(self):  # 返回自己的key
        return self.id

    def getWeight(self, nbr):  # 返回所连接ner顶点的权重是多少
        return self.connectedTo[nbr]

class taskVertext(Vertext):
    def __init__(self, key):            # key表示是添加的顶点
        super(taskVertext, self).__init__(key)
        self.distance = 0               # task 所在的层数，默认为0
        self.color = ColorTask.white    # task 路径搜索标志，默认白色
        self.prefix = None              # task 顶点的前驱顶点默认为None

'''
Graph包含了所有的顶点
包含了一个主表(临接列表)
'''


class Graph():  # 图 => 由顶点所构成的图

    '''
    存储图的方式是用邻接表实现的.

    数据结构: {
                key:Vertext(){
                    self.id = key
                    self.connectedTo{
                        相邻节点类实例 : 权重
                        ..
                        ..
                    }
                }
                ..
                ..
        }
    '''

    def __init__(self):
        self.vertList = {}  # 临接列表
        self.numVertices = 0  # 顶点个数初始化

    def addVertex(self, key):  # 添加顶点
        self.numVertices +=  1  # 顶点个数累加
        # newVertex = Vertext(key)  # 创建一个顶点的临接矩阵
        # newVertex = taskVertext(key)  # 创建一个顶点的临接矩阵
        newVertex = DFSVertext(key)  # 创建一个顶点的临接矩阵
        self.vertList[key] = newVertex
        return newVertex

    def getVertex(self, n):  # 通过key查找定点
        if n in self.vertList:
            return self.vertList[n]
        else:
            return None

    def getUpstreamVertex(self, key):
        """
        获取当指向前节点的所有顶点信息，包括间接指向的顶点信息
        :param key: 目标在图中的Name
        :return: 所有被target 直接或间接依赖的 Name
        """
        keyobject = self.getVertex(key)
        routeTask = []
        vertQueue = []  # 彎¢索轘~_佈~W﻾L佅~H达[佅~H佇º
        vertQueue.insert(0, keyobject)

        while len(vertQueue):
            currentVert = vertQueue.pop()
            # print(currentVert)
            keyobjects = currentVert.prefix
            for onekeyobject in keyobjects:
                if onekeyobject.id not in routeTask:
                    routeTask.append(onekeyobject.id)
                vertQueue.insert(0, onekeyobject)
        '''
        while keyobject.prefix != []:
            keyobjects = keyobject.prefix
            routeTask.extend([onekeyobject.id for onekeyobject in keyobjects])
            keyobject = keyobjects[0]
            print(routeTask)
            # routeTask.append(keyobject.id)  # 彊~J庠¹罊~B潂¹佊| ䷾J
        '''
        return routeTask


    def __contains__(self, n):  # transition:包含 => 返回所查询顶点是否存在于图中
        # print( 6 in g)
        return n in self.vertList

    def addEdge(self, f, t, cost=1):  # 添加一条边， 默认为有向图
        if f not in self.vertList:  # 如果没有边,就创建一条边
            nv = self.addVertex(f)
        if t not in self.vertList:  # 如果没有边,就创建一条边
            nv = self.addVertex(t)

        if cost == 0:  # cost == 0 代表是没有传入参数,而使用的默认参数1,默认为有向图
            self.vertList[f].addNeighbor(self.vertList[t], cost)  # cost是权重.无向图为0
            self.vertList[t].addNeighbor(self.vertList[f], cost)
        else:  #
            self.vertList[f].addNeighbor(self.vertList[t], cost)  # cost是权重

    def getVertices(self):  # 返回图中所有的定点
        return self.vertList.keys()

    def __iter__(self):  # return => 把顶点一个一个的迭代取出.
        return iter(self.vertList.values())

    # 广度优先搜索
    def BFSTraverse(self, key):
        keyobject = self.getVertex(key)
        vertQueue = []  # 探索队列，先进先出
        vertQueue.insert(0, keyobject)

        while len(vertQueue):
            currentVert = vertQueue.pop()
            for nbr in currentVert.getConnections():
                if nbr.color == ColorTask.white:
                    nbr.distance = currentVert.distance + 1
                    nbr.prefix = currentVert
                    currentVert.color = ColorTask.bary # 标记为正在探索
                    vertQueue.insert(0, nbr)
                currentVert.color = ColorTask.black # 标记为已探索

    def getPath(self, key):
        keyobject = self.getVertex(key)
        routeTask = []
        while keyobject.prefix != None:
            keyobject = keyobject.prefix
            routeTask.append(keyobject.id)
        # routeTask.append(keyobject.id)  # 把根节点加上
        return routeTask

def TestGraph():
    #
    # -------------------------------------------------
    # 以下是测试数据.可删除
    # -------------------------------------------------
    #
    g = Graph()

    # for i in range(6):
    #     g.addVertex(i)
    # print(g.vertList)

    '''
    # a = g.vertList[0]
    # print(a.connectedTo)
    '''

    g.addEdge(0, 5, 2)
    g.addEdge(1, 2, 4)
    g.addEdge(2, 3, 9)
    g.addEdge(3, 4, 7)
    g.addEdge(3, 5, 3)
    g.addEdge(4, 0, 1)
    g.addEdge(5, 4, 8)
    g.addEdge(5, 2, 1)

    print(g.getVertices())
    # vertList = { key :VertextObject}
    # VertextObject =  ||key = key, connectedTo = {到达节点:权重}||   => |||| 表示的是权重的意思

    # print(g)
    for v in g:  # 循环类实例 => return ->  g = VertextObject的集合  v = VertextObject
        for w in v.getConnections():  # 获得类实例的connectedTO
            # print(w)
            print("({},{}:{})".format(v.getId(), w.getId(), v.getWeight(w)))  ## 为什么会是这样 => 因为这个时候v就是class啊

# 带有深度优先算法的图
class DFSVertext(Vertext):
    def __init__(self, key):
        self.st = 0         # 顶点开始被探索的时间点
        self.et = 0         # 顶点被探索完成的时间点
        self.distance = 0   # task 所在的层数，默认为0
        self.color = ColorTask.white
        self.prefix = []  # 记录顶点的父节点的列表
        super(DFSVertext, self).__init__(key)

class DFSGraph(Graph):
    def __init__(self):
        super(DFSGraph, self).__init__()
        self.time = 0
        self.glob_distance = 0

    def defineDepth(self):
        for aVertext in self.vertList.values():
            # 对该节点的相邻节点进行探索
            vertQueue = []  # 探索队列，先进先出
            vertQueue.insert(0, aVertext)

            while len(vertQueue):
                currentVert = vertQueue.pop()
                for nbr in currentVert.getConnections():
                    # print(currentVert.id, nbr.id, nbr.color)
                    # if nbr.color == ColorTask.white:
                    nbr.distance = currentVert.distance + 1
                    if currentVert not in nbr.prefix:nbr.prefix.append(currentVert)
                    currentVert.color = ColorTask.bary  # 标记为正在探索
                    vertQueue.insert(0, nbr)
                    currentVert.color = ColorTask.black  # 标记为已探索

    def distancelayer(self, aVertext):
        if aVertext.getConnections() == {}:
            return
        for nbr in aVertext.getConnections():
            self.distancelayer(nbr)
            nbr.distance = self.glob_distance
        self.glob_distance += 1
        return

    def dfs(self):
        """
        深度优先算法对图构建树或者森林
        :return:
        """
        for aVertext in self.vertList.values():
            aVertext.color = ColorTask.white
            aVertext.prefix = []

        # 开始探索所有的顶点
        for aVertext in self.vertList.values():
            if aVertext.color == ColorTask.white:
                self.explore(aVertext)

    def explore(self, aVertext):
        """
        探索节点 - 不停的往节点的下层找相邻节点
        :param aVertext:
        :return:
        """
        aVertext.color = ColorTask.bary
        self.time += 1
        aVertext.st = self.time

        # 对该节点的相邻节点进行探索
        for nbr in aVertext.getConnections():
            # print(aVertext.id, nbr.id, nbr.color)
            # if nbr.color == ColorTask.white:
            nbr.distance = aVertext.distance + 1
            if aVertext not in nbr.prefix:
                nbr.prefix.append(aVertext)
            self.explore(nbr)

        # 探索完该节点和该节点的所有下层节点后
        aVertext.color = ColorTask.black
        self.time += 1
        aVertext.et = self.time
