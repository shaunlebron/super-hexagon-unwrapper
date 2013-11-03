# This is a special heap that we need for the polygon reduction algorithm.

class EmptyHeapException(Exception):
	def __init__(self,msg):
		self.msg = msg

class Heap:
	"""
	This is a generic binary heap with the following constructor arguments:
		* nodes: sequence of objects of any type
		* is_higher: function(a,b) returning true if 'a' is higher priority than 'b'
		* on_index_change: callback function(node,i) called when 'node' changes to index 'i'
	"""

	def __init__(self, nodes, is_higher, on_index_change=None):
		self.array = []
		self.is_higher = is_higher
		self.on_index_change = on_index_change
		for node in nodes:
			self.push(node)

	def normalize_index(self,i):
		return i if (0 <= i and i < len(self.array)) else None
	
	def get_parent_index(self,i):
		return self.normalize_index((i+1)/2 - 1)

	def get_child_indexes(self,i):
		i = (i+1)*2 - 1
		return self.normalize_index(i), self.normalize_index(i+1)

	def place_node_at_index(self,node,i):
		self.array[i] = node
		if self.on_index_change:
			self.on_index_change(node, i)
	
	def swap_nodes(self,i0,i1):
		node0 = self.array[i0]
		node1 = self.array[i1]
		self.place_node_at_index(node0, i1)
		self.place_node_at_index(node1, i0)

	def is_index_higher(self,i0,i1):
		if i0 is None or i1 is None:
			return False
		return self.is_higher(self.array[i0],self.array[i1])
	
	def try_promote_node(self,i):
		parent_i = self.get_parent_index(i)
		if self.is_index_higher(i, parent_i):
			self.swap_nodes(i, parent_i)
			self.try_promote_node(parent_i)
	
	def try_demote_node(self,i):
		child_i, next_child_i = self.get_child_indexes(i)
		if self.is_index_higher(next_child_i, child_i):
			child_i = next_child_i
		if self.is_index_higher(child_i, i):
			self.swap_nodes(i, child_i)
			self.try_demote_node(child_i)

	def reorder_node(self,i):
		self.try_promote_node(i)
		self.try_demote_node(i)

	def push(self, node):
		self.array.append(None)
		i = len(self.array)-1
		self.place_node_at_index(node,i)
		self.try_promote_node(i)
	
	def peek(self):
		if not self.array:
			raise EmptyHeapException('cannot peek at empty heap')
		return self.array[0]
	
	def pop(self):

		# stop if nothing to pop
		if not self.array:
			raise EmptyHeapException('cannot pop empty heap')

		# get root node, and nullify its index
		node = self.array[0]
		if self.on_index_change:
			self.on_index_change(node, None)

		# replace root node with last node
		self.place_node_at_index(self.array[-1], 0)

		# remove last node
		self.array.pop()

		# re-order heap from new root node
		if len(self.array) > 1:
			self.try_demote_node(0)

		# return the popped node
		return node

######################################################################

import unittest
import random

class TestHeapOrder(unittest.TestCase):
	def setUp(self):
		self.count = 1000
		self.elements = [random.randint(1,50) for i in xrange(self.count)]
		def is_higher(a,b):
			return a < b
		self.heap = Heap(self.elements, is_higher)
	
	def assert_order(self):
		prev_a = self.heap.pop()
		num_popped = 1
		while True:
			try:
				a = self.heap.pop()
				num_popped += 1
				self.assertLessEqual(prev_a, a)
				prev_a = a
			except EmptyHeapException:
				break
		self.assertEqual(num_popped, self.count)
	
	def test_initial_order(self):
		self.assert_order()
	
	def change_value_at_index(self, i):
		self.heap.array[i] = random.randint(1,50)
		self.heap.reorder_node(i)
	
	def test_reorder(self):
		for i in xrange(self.count):
			self.change_value_at_index(random.randrange(self.count))
		self.assert_order()

if __name__ == "__main__":
	unittest.main()
