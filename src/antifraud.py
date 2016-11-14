import warnings
import time
import sys

class Graph:
    ''' Undirected social network graph based on batch file. '''
    
    def __init__(self, batchFileName, skipHeader):
        self.batchFileName = batchFileName
        self.__buildGraph(batchFileName, skipHeader)

        
    def __buildGraph(self, filename, skipHeader = True):
        ''' Reads given batch dataset and constructs a graph.'''
        self.adjacencyList = {}
    
        with open(filename, 'r') as f:
            for index, row in enumerate(f):
                if skipHeader == True:
                    skipHeader = False
                    continue
                self.addToGraph(row, index)


    def parseTransaction(self, row):
        items = row.split(",", 4)
        assert(len(items)) == 5
         
        id1 = int(items[1])
        id2 = int(items[2])
    
        #TODO Implement other attributes and encode then into adjecency list for more detection features
        return None, id1, id2, None, None


    def addToGraph(self, row, index):
        try:
            transaction = self.parseTransaction(row)
        except:
            warnings.warn(" Skipped adding unparseable transaction at line " + str(index), Warning)
        else:    
            _, id1, id2, _, _ = transaction # discard all but id1 and id2
        
            if id1 == id2:
                return # self-transactions are irrelavant
            
            try:
                self.adjacencyList[id1].add(id2)
            except KeyError:
                self.adjacencyList[id1] = set([id2])
        
            try:
                self.adjacencyList[id2].add(id1)
            except KeyError:
                self.adjacencyList[id2] = set([id1])
        
    
    def getNeighbors(self, node):
        try:
            return self.adjacencyList[node]
        except KeyError:
            return None
            

def findConnectionDegree(graph, source, target, max_depth):
    ''' Returns degree of connection between source and target in the graph using iterative deepening DFS. 
        Returns None if not connected within degree = max_depth.'''

    def DLS(node, depth):
        ''' Recursive depth-limited DFS. '''
        if depth == 0 and node == target:
            return node
        if depth > 0:
            for child in graph.getNeighbors(node):
                found = DLS(child, depth - 1)
                if found != None:
                    return found
        return None

    # corner case where either source or target isn't in graph
    if (source not in graph.adjacencyList) or (target not in graph.adjacencyList):
        return None

    # corner case where source = target != null
    if source == target and source != None:
        return 0


    # begin ID-DFS
    for depth in range(max_depth + 1):
        found = DLS(source, depth)
        if found != None:
            return depth


def processStream(graph, inputStreamFile, outputStreamFile, feature, skipHeader=True):
    '''Contructs graph and processes input stream files. 
    Returns line count when input stream file finishes for benchmarking purposes'''
    with open(inputStreamFile, 'r') as inputStream, open(outputStreamFile, 'w') as outputStream:

        lineCount = 0 # counting for later benchmarking

        for index, row in enumerate(inputStream):
            if skipHeader == True:
                skipHeader = False
                continue

            try:
                transaction = graph.parseTransaction(row)

            except:
                # Note: Mark unverified if parsing fails to avoid taking risk
                outputStream.write("unverified\n")
                warnings.warn(" Skipped adding unparseable transaction at line " + str(index), Warning)                

            else:    
                _, id1, id2, _, _ = transaction # discard all but id1 and id2
                
                if feature==1:
                    outputStr = "unverified\n" if findConnectionDegree(graph, id1, id2, 1) == None else "trusted\n"
                elif feature==2:
                    outputStr = "unverified\n" if findConnectionDegree(graph, id1, id2, 2) == None else "trusted\n"
                elif feature==3:
                    outputStr = "unverified\n" if findConnectionDegree(graph, id1, id2, 4) == None else "trusted\n"
                else:
                    raise ValueError("Invalid feature value")

                outputStream.write(outputStr)

            lineCount += 1
    return lineCount


if __name__ == "__main__":
    def processAll(batch_input, stream_input, output_folder):
        '''Run script for all three features and time execution for each'''
        print "Constructing graph from batch file...", 
        start_time = time.time()
        graph = Graph(batch_input, True)
        print("%s sec" % (time.time() - start_time))
        
        for feature in [1,2,3]:
            stream_output = output_folder + "/output" + str(feature) + ".txt"
            print "Processing stream file and saving feature %d output..." %feature, 
            start_time = time.time()
            lineCount = processStream(graph, stream_input, stream_output, feature)
            print("%0.4s sec total, %.12f sec per transaction (avg)" % (time.time() - start_time, (time.time() - start_time)/float(lineCount)))    

    if len(sys.argv) == 4:
        batch_input = sys.argv[1]
        stream_input = sys.argv[2]
        output_folder = sys.argv[3]
        processAll(batch_input, stream_input, output_folder)

    elif len(sys.argv) == 2:
        batch_input = "../insight_testsuite/tests/" + sys.argv[1] + "/paymo_input/batch_payment.txt"
        stream_input = "../insight_testsuite/tests/" + sys.argv[1] + "/paymo_input/stream_payment.txt"
        output_folder = "../insight_testsuite/tests/" + sys.argv[1] + "/paymo_output/"
        processAll(batch_input, stream_input, output_folder)
    

    else:
        print "Usage 1: specify batch, input file and output folder\nSyntax:\n\tpython antifraud.py <batch payment file> <stream payment file> <output path>\ne.g.\n\tpython antifraud.py ../paymo_input/batch_payment.csv ../paymo_input/stream_payment.csv ../paymo_output\n"
        print "Usage 2: specify test case folder name inside insight_testsuit/tests folder\nSyntax:\n\tpython antifraud.py <test case name>\ne.g.\n\tpython antifraud.py test-2-graph-search"
        
