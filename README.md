# Submission for Insight Data Engineering Challenge Jan 2017
## An optimized and scalable fraud detection module for Paymo using Iterative Deepening DFS on Hashmap adjacency-list based graph representation 

## Problem
Given a list of transactions between two users (batch data), determine trustworthiness of given transaction (streaming data) using 3 different rules:

* Rule/Feature 1: Check if a prior transaction has occurred between two parties. 
* Rule/Feature 2: Check for triadic closure / 2nd degree relationship 
* Rule/Feature 3: Check for transitive closure of at most 4 degrees. i.e. check if two parties are connected by at most 3 people in between.

For each transaction the program returns "trusted" if one of the above rules satisfy and "unverified" otherwise. Only one rule is applied on the streaming data at a time and saved into respective files: output1.txt, output2.txt and so on.

## Approach
### 1. Graph Construction
A social network can be represented by a graph. Each node can represent a person. Any transaction between two persons would connect their respective nodes. This connection is called an edge. Let V be the set of nodes or vertices in this graph and E be the set of edges.

From the nature of the problem and data, the following can be observed about representation of the graph:

1. The graph would be sparsely connected. i.e. |E| << |V|^2. This is because the users are performing transactions with few other used compared to the no. of users in the graph. So the total edges is much lesser that max possible no. of edges in a graph which is |V|^2.
  

2. Since we will be traversing through graph often as we search for connectivity between two users, it is important to optimize query time.

Consider the figure below (adapted from Wikipedia):
![fig1](/images/fig-adj_list.png)

There are multiple ways of representing the graph and in this implementation, an adjacency list using hashmap is chosen for the following reasons:

1. A matrix representation would waste memory space because it requires O(|V|^2) space but the graph is sparsely connected i.e. |E| << |V|^2.

2. The adjacency list is implemented as a Hash table to optimize for:
	* Query: Needed for any access to a node. Most frequently called operation.
	* Adding edge: It is desirable in future to be able to add approved transactions into the graph without re-building it.
	* Remove edge: It is desirable in future to remove users and their nodes as their accounts deactivate. 

####Data Structure
The data structure that implements adjacency list is a Python dictionary (hashmap) where each key represents node and value contains a set of neighboring nodes. When assigning neighbors, the python set() operation (performs hashing) performs de-duplication.

**Pseudocode**

	# process line by line from batch file
	f = openFile(batchFile)
	adjacencyList = {}
	for each line in f
		# get nodes
		id1, id2 <- parseLine(line)

		if id1 in adjacencyList
			# add to its neighbor set
			adjacencyList[id1].add(id2)
		else
			# initialize set with one item 
			adjacencyList[id1] <- set([id2])

		# repeating for undirected graph
		if id2 in adjacencyList
			# add to its neighbor set
			adjacencyList[id2].add(id1)
		else
			# initialize set with one item 
			adjacencyList[id2] <- set([id1])

###Example
The test-case: **test-2-graph-search** contained in \insight_test_suite\tests\ looks like the following:
![fig2](/images/fig-sample_graph.png)

The adjacencyList looks like the following in Python:

	>> print graph.adjacencyList
	{0: {1},
	 1: {0, 2, 4},
	 2: {1, 3},
	 3: {2, 4, 5},
	 4: {1, 3},
	 5: {3, 6},
	 6: {5, 7},
	 7: {6},
	 8: {9, 10, 11},
	 9: {8},
	 10: {8},
	 11: {8}}

Notice that columns in transaction record such as time-stamp, amount and message are not being used and are therefore not being added to adjacencyList. **If a feature requires, these can be added into node value which contains only neighbor set presently. An example would be saving the last 10 payments made by the user and flagging a transaction when the amount being sent is 2 std dev away from the mean.**

#### Special cases
1. Loops or self-transaction if allowed by the service, aren't added this graph because these are irrelevant for the task of fraud detection.

2. Since multiple edges connecting same two nodes do not give additional information, a multigraph is not required. 

3. The graph is undirected. The direction of payment does not affect the relationship.


### 2. Graph Search
Once the graph is constructed from batch payment data, the next step is to be able to find degree of connection between two users given in stream data.

Finding the degree of connection is the problem of finding if length of shortest path between two nodes, where distance of each edge is 1.

There are two ways of doing this:

1. Using dynamic programming to find and store all shortest paths: Floyd-Warshall algorithms and its variants fall under this category. Although this may look like an efficient approach, the problem is that adding edges or removing vertices will require re-computation of shortest paths and it is therefore not scalable. 

2. Find shortest-path between two giving edge: A natural way of doing this would be Dijkstra's algorithm for shortest path and it's variants. However, in this problem, we're limited to find degree of connections not larger than 4. This means that during path search, we do not have to traverse beyond 4 steps. The iterative deepening DFS would take advantage of this fact and hence this is being used.

**Pseudocode:**

	function IDDFS(root, depth)
	    for depth from 0 to max_depth
	        found ← DLS(root, depth)
	        if found ≠ null
	            return depth
	
	function DLS(node, depth)
	    if depth = 0 and node is a goal
	        return node
	    if depth > 0
	        foreach child of node
	            found ← DLS(child, depth−1)
	            if found ≠ null
	                return found
	    return null

The time complexity is O(*b*^*d*) and space-complexity is O(*b***d*). *b* is the branching factor. The average branching factor would be the average no. of users each user is connected to. Therefore *b* is expected to be low. Depth *d* is 4 in this case. Therefore, this algorithms appears suitable to the problem.

The implementation can be used to implement feature 1 and 2 with d = 1 and 2 respectively.


##Usage
The following module implements the functionality on **Python 2.7**:

	\src\antifraud.py

Syntax 1: specify batch, input file and output folder

	python antifraud.py <batch payment file> <stream payment file> <output path>

e.g.
	
	python antifraud.py ../paymo_input/batch_payment.csv ../paymo_input stream_payment.csv ../paymo_output/

Syntax 2: specify test case folder name inside insight_testsuit/tests folder
	python antifraud.py <test case name>

e.g.

	python antifraud.py test-2-graph-search

### Demo
Running test-case: **test-2-graph-search** contained in \insight_test_suite\tests\

#### Inputs (only id1 and id2 are relevant):

batch_payment.txt contents:
	
	time, id1, id2, amount, message
	2016-11-02 09:49:29, 0, 1, 25.32, Spam 
	2016-11-02 09:49:29, 2, 1, 19.45, Food for 🌽 😎 
	2016-11-02 09:49:29, 4, 3, 14.99, Clothing 
	2016-11-02 09:49:29, 2, 3, 13.48, LoveWins 
	2016-11-02 09:49:29, 8, 9, 29.94, Jeffs still fat 
	2016-11-02 09:49:29, 3, 5, 19.01, 🌞🍻🌲🏔🍆
	2016-11-02 09:49:29, 7, 6, 25.32, Spam 
	2016-11-02 09:49:29, 10, 8, 19.45, Food for 🌽 😎 
	2016-11-02 09:49:29, 6, 5, 14.99, Clothing 
	2016-11-02 09:49:29, 1, 4, 13.48, LoveWins 
	2016-11-02 09:49:29, 11, 8, 29.94, Jeffs still fat 

stream_payment.txt contents:

	time, id1, id2, amount, message
	2016-11-02 09:49:29, 0, 5, 25.32, 0-0-1
	2016-11-02 09:49:29, 0, 1, 19.45, 1-1-1
	2016-11-02 09:49:29, 4, 2, 14.99, 0-1-1 
	2016-11-02 09:49:29, 10, 3, 13.48, 0-0-0 
	2016-11-02 09:49:29, 0, 5, 29.94, 0-0-1
	2016-11-02 09:49:29, 4, 2, 19.01, 0-1-1
	2016-11-02 09:49:29, 4, 7, 25.32, 0-0-1 
	2016-11-02 09:49:29, 0, 6, 19.45, 0-0-0
	2016-11-02 09:49:29, 1, 7, 14.99, 0-0-0
	2016-11-02 09:49:29, 10, 9, 13.48, 0-1-1
	2016-11-02 09:49:29, 11, 11, 29.94, 1-1-1

#### Output (only id1 and id2 are relevant):

**Feature 1:** output1.txt contents:
	
	unverified
	trusted
	unverified
	unverified
	unverified
	unverified
	unverified
	unverified
	unverified
	unverified
	trusted

**Feature 2:** output2.txt contents:

	unverified
	trusted
	trusted
	unverified
	unverified
	trusted
	unverified
	unverified
	unverified
	trusted
	trusted

**Feature 3:** output3.txt contents:
	
	trusted
	trusted
	trusted
	unverified
	trusted
	trusted
	trusted
	unverified
	unverified
	trusted
	trusted

Graph is pasted again for convenience and the results can be verified by looking at it:

![fig2](/images/fig-sample_graph.png)


##Results
antifraud.py was run on supplied real data found on:

[batch_payment.csv](https://www.dropbox.com/s/y6fige3w1ohksbd/batch_payment.csv?dl=0)

[stream_payment.csv](https://www.dropbox.com/s/vrn4pjlypwa2ki9/stream_payment.csv?dl=0)

	Constructing graph from batch file... 14.1080000401 sec.
	Processing stream file and saving feature 1 output... 24.3 sec total, 0.000008124000 sec per transaction (avg)
	Processing stream file and saving feature 2 output... 600 sec total, 0.000200084000 sec per transaction (avg)
	Processing stream file and saving feature 3 output...

outputs generated by this program:

[output1.txt](https://drive.google.com/file/d/0Bz9J5qV6mHiZZVZQc2t1aEUwVHM/view?usp=sharing)

[output2.txt](https://drive.google.com/file/d/0Bz9J5qV6mHiZUkFfS0RGeDlndzA/view?usp=sharing)

[output3.txt] coming soon..