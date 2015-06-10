from np import trunc, log

from __future__ import division

def find_i_j(x, y, z):
	"""
	finds the combination of i and j which minimizes the number of wasted
	pixels for input images of dimensions x and y with number of images z
	"""
	max_n = trunc(log(z * x, 2)) + 1 # n value required if all images in i direction
	max_m = trunc(log(z * y, 2)) + 1 # m value required if all images in j direction

	solutions = [] # hold n, m and the number of wasted pixels for a solution
	sol_num = 0

	for n in range(1, max_n + 1):
		for m in range(1, max_m + 1):
			if((2**n / x) * (2**m / y) >= z):
				# determines if a tile of with dimesions of n and m can contain
				# all the images

				sol_info = []
				sol_info.append(n)
				sol_info.append(m)
				sol_info.append(waste_det(x, y, z, n, m))

				solutions.append(sol_info)

				sol_num += 1

	sol_total = sol_num # records total number of solutions

	opt = find_waste_min(sol_total, solutions) # gets properties of optimal solution

	i = 2**opt[1]
	j = 2**opt[2]

	tile_dim = [i, j]
	return tile_dim


def find_waste_min(sol_total, solutions):
	"""
	finds solution with the lowest number of wasted pixels
	"""

	waste_min = solutions[0][2] + 1

	for sol_num in range(0, sol_total): # finds solution with lowest waste
		if(waste_min > solutions[sol_num][2]):
			opt = []

			waste_min = solutions[sol_num][2]
			n = solutions[sol_num][0]
			m = solutions[sol_num][1]

			opt.append(waste_min)
			opt.append(n)
			opt.append(m)

	return opt


def waste_det(x, y, z, n, m):
	"""
	determines the number of dead pixels for given image properties (x, y, z)
	and tile properties (n, m)
	"""
	dead_pixels = 2**(n+m) - x * y * z
	return dead_pixels
