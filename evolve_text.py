"""
Evolutionary algorithm, attempts to evolve a given message string.

Uses the DEAP (Distributed Evolutionary Algorithms in Python) framework,
http://deap.readthedocs.org

Usage:
	python evolve_text.py [goal_message]

Full instructions are at:
https://sites.google.com/site/sd15spring/home/project-toolbox/evolutionary-algorithms
"""

import random
import string

import numpy    # Used for statistics
from deap import algorithms
from deap import base
from deap import tools


#-----------------------------------------------------------------------------
# Global variables
#-----------------------------------------------------------------------------

# Allowable characters include all uppercase letters and space
# You can change these, just be consistent (e.g. in mutate operator)
VALID_CHARS = string.ascii_uppercase + " "

# Control whether all Messages are printed as they are evaluated
VERBOSE = True

LEV_DICT = {}

#-----------------------------------------------------------------------------
# Message object to use in evolutionary algorithm
#-----------------------------------------------------------------------------

class FitnessMinimizeSingle(base.Fitness):
	"""
	Class representing the fitness of a given individual, with a single
	objective that we want to minimize (weight = -1)
	"""
	weights = (-1.0, )


class Message(list):
	"""
	Representation of an individual Message within the population to be evolved

	We represent the Message as a list of characters (mutable) so it can
	be more easily manipulated by the genetic operators.
	"""
	def __init__(self, starting_string=None, min_length=4, max_length=30):
		"""
		Create a new Message individual.

		If starting_string is given, initialize the Message with the
		provided string message. Otherwise, initialize to a random string
		message with length between min_length and max_length.
		"""
		# Want to minimize a single objective: distance from the goal message
		self.fitness = FitnessMinimizeSingle()

		# Populate Message using starting_string, if given
		if starting_string:
			self.extend(list(starting_string))

		# Otherwise, select an initial length between min and max
		# and populate Message with that many random characters
		else:
			initial_length = random.randint(min_length, max_length)
			for i in range(initial_length):
				self.append(random.choice(VALID_CHARS))

	def __repr__(self):
		"""Return a string representation of the Message"""
		# Note: __repr__ (if it exists) is called by __str__. It should provide
		#       the most unambiguous representation of the object possible, and
		#       ideally eval(repr(obj)) == obj
		# See also: http://stackoverflow.com/questions/1436703
		template = '{cls}({val!r})'
		return template.format(cls=self.__class__.__name__,     # "Message"
							   val=self.get_text())

	def get_text(self):
		"""Return Message as string (rather than actual list of characters)"""
		return "".join(self)


#-----------------------------------------------------------------------------
# Genetic operators
#-----------------------------------------------------------------------------

# TODO: Implement levenshtein_distance function (see Day 9 in-class exercises)
# HINT: Now would be a great time to implement memoization if you haven't


def levenshtein_distance(a, b):
	"""
	Computes the Levenshtein distance between two input strings
	"""

	if (a,b) in LEV_DICT:
		return LEV_DICT[(a,b)]

	if a == "":
		return len(b)
	if b == "":
		return len(a)

	if a[0] == b[0]:
		option1 = levenshtein_distance(a[1:], b[1:])
	else:
		option1 = 1 + levenshtein_distance(a[1:], b[1:])

	option2 = 1 + levenshtein_distance(a, b[1:])
	option3 = 1 + levenshtein_distance(a[1:], b)

	distance = min(option1, option2, option3)
	LEV_DICT[(a,b)] = distance

	return distance

def evaluate_text(message, goal_text, verbose=VERBOSE):
	"""
	Given a Message and a goal_text string, return the Levenshtein distance
	between the Message and the goal_text as a length 1 tuple.
	If verbose is True, print each Message as it is evaluated.
	"""
	distance = levenshtein_distance(message.get_text(), goal_text)
	if verbose:
		print "{msg:60}\t[Distance: {dst}]".format(msg=message, dst=distance)
	return (distance, )     # Length 1 tuple, required by DEAP


def mutate_text(message, prob_ins=0.05, prob_del=0.05, prob_sub=0.05):
	"""
	Given a Message and independent probabilities for each mutation type,
	return a length 1 tuple containing the mutated Message.

	Possible mutations are:
		Insertion:      Insert a random (legal) character somewhere into
						the Message
		Deletion:       Delete one of the characters from the Message
		Substitution:   Replace one character of the Message with a random
						(legal) character
	"""
	# insert a character
	if random.random() < prob_ins:
		mutation_index = random.randint(0, len(message)-1)
		mutation_character = random.choice(VALID_CHARS)
		message.insert(mutation_index, mutation_character)
	# delete a character
	if random.random() < prob_del:
		mutation_index = random.randint(0, len(message)-1)
		del message[mutation_index]
	# replace a character with a new character
	if random.random() < prob_sub:
		mutation_index = random.randint(0, len(message)-1)
		mutation_character = random.choice(VALID_CHARS)
		message[mutation_index] = mutation_character

	return (message, )   # Length 1 tuple, required by DEAP


#-----------------------------------------------------------------------------
# DEAP Toolbox and Algorithm setup
#-----------------------------------------------------------------------------

def dna_swap(string1, string2):
	"""
	Swaps a random selection of charchters from two strings and returns two modified strings of the same original length
	"""
	
	string_length = min(len(string1), len(string2))
	swap_start = random.randint(1, string_length)
	swap_length = random.randint(1, string_length-swap_start+1)
	swap_end = swap_start + swap_length

	string1[swap_start:swap_end], string2[swap_start:swap_end] = string2[swap_start:swap_end], string1[swap_start:swap_end]
	
	return string1, string2

def get_toolbox(text):
	"""Return DEAP Toolbox configured to evolve given 'text' string"""

	# The DEAP Toolbox allows you to register aliases for functions,
	# which can then be called as "toolbox.function"
	toolbox = base.Toolbox()

	# Creating population to be evolved
	toolbox.register("individual", Message)
	toolbox.register("population", tools.initRepeat, list, toolbox.individual)

	# Genetic operators
	toolbox.register("evaluate", evaluate_text, goal_text=text)
	toolbox.register("mate", dna_swap)
	toolbox.register("mutate", mutate_text)
	toolbox.register("select", tools.selTournament, tournsize=3)

	# NOTE: You can also pass function arguments as you define aliases, e.g.
	#   toolbox.register("individual", Message, max_length=200)
	#   toolbox.register("mutate", mutate_text, prob_sub=0.18)

	return toolbox


def evolve_string(text):
	"""Use evolutionary algorithm (EA) to evolve 'text' string"""

	# Set random number generator initial seed so that results are repeatable.
	# See: https://docs.python.org/2/library/random.html#random.seed
	#      and http://xkcd.com/221
	random.seed(4)

	# Get configured toolbox and create a population of random Messages
	toolbox = get_toolbox(text)
	pop = toolbox.population(n=200)

	# Collect statistics as the EA runs
	stats = tools.Statistics(lambda ind: ind.fitness.values)
	stats.register("avg", numpy.mean)
	stats.register("std", numpy.std)
	stats.register("min", numpy.min)
	stats.register("max", numpy.max)

	# Run simple EA
	# (See: http://deap.gel.ulaval.ca/doc/dev/api/algo.html for details)
	pop, log = algorithms.eaSimple(pop,
								   toolbox,
								   cxpb=0.5,    # Prob. of crossover (mating)
								   mutpb=0.2,   # Probability of mutation
								   ngen=20,    # Num. of generations to run
								   stats=stats)

	return pop, log


#-----------------------------------------------------------------------------
# Run if called from the command line
#-----------------------------------------------------------------------------

if __name__ == "__main__":

	# Get goal message from command line (optional)
	import sys
	if len(sys.argv) == 1:
		# Default goal of the evolutionary algorithm if not specified.
		# Pretty much the opposite of http://xkcd.com/534
		goal = "SKYNET IS NOW ONLINE"
	else:
		goal = " ".join(sys.argv[1:])

	# Verify that specified goal contains only known valid characters
	# (otherwise we'll never be able to evolve that string)
	for char in goal:
		if char not in VALID_CHARS:
			msg = "Given text {goal!r} contains illegal character {char!r}.\n"
			msg += "Valid set: {val!r}\n"
			raise ValueError(msg.format(goal=goal, char=char, val=VALID_CHARS))

	# Run evolutionary algorithm
	pop, log = evolve_string(goal)
