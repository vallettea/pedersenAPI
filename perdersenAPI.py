import os, sys, json, time
import numpy as np
import igraph
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
from matplotlib.collections import PatchCollection


class BBShell:
	def __init__(self, diameter, length):
		self.diameter = diameter
		self.length = length
		self.radius = diameter/2.

	def patch(self):
		return mpatches.Circle((0., 0.), self.radius, fill = False, ec = "k", lw = 2)

class Tube:
	def __init__(self, diameter, start, end):
		self.diameter = diameter
		self.start = start
		self.end = end
		
	def patch(self):
		verts = [self.start, self.end]
		codes = [Path.MOVETO, Path.LINETO]
		path = Path(verts, codes)
		return mpatches.PathPatch(path, lw=2)

class Frame:
	def __init__(self, alpha1, alpha2, alpha3, l1, l2, l3, l4, bbshell):
		self.alpha1 = alpha1
		self.alpha2 = alpha2
		self.alpha3 = alpha3
		self.l1 = l1
		self.l2 = l2
		self.l3 = l3
		self.l4 = l4
		self.bbshell = bbshell
		self.components = [self.bbshell]

	def assemble(self):
		start = (self.bbshell.radius * np.cos(np.deg2rad(self.alpha1)), self.bbshell.radius * np.sin(np.deg2rad(self.alpha1)))
		end = (self.l1 * np.cos(np.deg2rad(self.alpha1)), self.l1 * np.sin(np.deg2rad(self.alpha1)))
		tube1 = Tube(20, start, end)

		start = (self.bbshell.radius * np.cos(np.deg2rad(self.alpha2)), self.bbshell.radius * np.sin(np.deg2rad(self.alpha2)))
		end = (self.l2 * np.cos(np.deg2rad(self.alpha2)), self.l2 * np.sin(np.deg2rad(self.alpha2)))
		tube2 = Tube(20, start, end)

		start = (self.bbshell.radius * np.cos(np.deg2rad(self.alpha3)), self.bbshell.radius * np.sin(np.deg2rad(self.alpha3)))
		end = (self.l3 * np.cos(np.deg2rad(self.alpha3)), self.l3 * np.sin(np.deg2rad(self.alpha3)))
		tube3 = Tube(20, start, end)

		tube4 = Tube(20, (-self.bbshell.radius, 0), (-self.l4, 0))

		tube5 = Tube(20, (-self.l4, 0), (self.l3 * np.cos(np.deg2rad(self.alpha3)), self.l3 * np.sin(np.deg2rad(self.alpha3))))

		tube6 = Tube(20, (-self.l4, 0), (self.l2 * np.cos(np.deg2rad(self.alpha2)), self.l2 * np.sin(np.deg2rad(self.alpha2))))
	
		self.components += [tube1, tube2, tube3, tube4, tube5, tube6]

	def plot_schema(self):

		patches = [x.patch() for x in self.components]

		collection = PatchCollection(patches, match_original = True)
		fig = plt.figure(figsize = (9, 9))
		ax = fig.add_subplot(111)
		ax.add_collection(collection)

		plt.axis("equal")
	
		plt.show()

bbshell = BBShell(68, 100)

frame = Frame(25, 70, 140, 800, 1000, 1100, 800, bbshell)
frame.assemble()
frame.plot_schema()