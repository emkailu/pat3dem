#!/usr/bin/env python

import os
import sys
import argparse
import pat3dem.star as p3s

def main():
	progname = os.path.basename(sys.argv[0])
	usage = progname + """ [options] <star files>
	Output the coordinates from star files. Origin offsets will be considered as float.
	"""
	
	args_def = {'box':-1, 'edge':-1, 'x':3710, 'y':3838, 'flip':''}	
	parser = argparse.ArgumentParser()
	parser.add_argument("star", nargs='*', help="specify star files to be processed")
	parser.add_argument("-b", "--box", type=int, help="specify a box size (in pixel) for output, by default {} (output .star only)".format(args_def['box']))
	parser.add_argument("-e", "--edge", type=int, help="specify a distance (in pixel) between box center and micrograph edge, by default {} (don't exclude edge)".format(args_def['edge']))
	parser.add_argument("-x", "--x", type=int, help="provide the x dimension (in pixel) of micrographs, by default {}. This option is unnessary unless you use the --edge option".format(args_def['x']))
	parser.add_argument("-y", "--y", type=int, help="provide the y dimension (in pixel) of micrographs, by default {}".format(args_def['y']))
	parser.add_argument("-f", "--flip", type=str, help="flip in which direction, by default {}. i.e., if flip in y (upside down), then y_new = args.y - y_old, do specify the correct args.x and args.y".format(args_def['flip']))
	args = parser.parse_args()
	
	if len(sys.argv) == 1:
		print "usage: " + usage
		print "Please run '" + progname + " -h' for detailed options."
		sys.exit(1)
	# get default values
	for i in args_def:
		if args.__dict__[i] == None:
			args.__dict__[i] = args_def[i]
	# loop over all input files		
	for star in args.star:
		star_dict = p3s.star_parse(star, 'data_')
		header_len = len(star_dict['data_'])+len(star_dict['loop_'])
		# if the star is after the particle extraction step
		if '_rlnImageName' in star_dict:
			out_dict = {}
			with open(star) as s_read:
				lines = s_read.readlines()[header_len:-1]
				# loop over lines, generate a dict: {out_name:[{ptcl#:line#}]}
				for j, line in enumerate(lines):
					line = line.split()
					num, rlnImageName = line[star_dict['_rlnImageName']].split('@')
					# name the output by _rlnImageName
					out_name = os.path.basename(os.path.splitext(rlnImageName[:-5])[0])
					out_dict[out_name] = out_dict.get(out_name, []) + [{num:j}]
				# loop over out_dict, write coords for each key
				for out_name in out_dict:
					out = out_name+'.star'
					if args.box != -1:
						out_box = out_name+'.box'
						o_box_write = open(out_box, 'a')
					with open(out, 'a') as o_write:
						o_write.write('\ndata_\n\nloop_ \n_rlnCoordinateX #1 \n_rlnCoordinateY #2 \n')
						# the value of outname is a list, containing dictionaries, which is sorted by the keys (ptcl#) of the dictionaries
						for d in sorted(out_dict[out_name]):
							line = lines[d.values()[0]].split()
							# get old coord
							x, y = float(line[star_dict['_rlnCoordinateX']]), float(line[star_dict['_rlnCoordinateY']])
							# calculate new coord
							if '_rlnOriginX' in star_dict:
								x -= float(line[star_dict['_rlnOriginX']])
								y -= float(line[star_dict['_rlnOriginY']])
							# flip
							if args.flip == 'x':
								x = args.x - x
							elif args.flip == 'y':
								y = args.y - y
							# exclude the edge
							if args.edge != -1:
								if not args.edge<=x<=args.x-args.edge or not args.edge<=y<=args.y-args.edge:
									continue
							o_write.write('{:>12} '.format(x) + '{:>12} \n'.format(y))
							if args.box != -1:
								o_box_write.write('{}'.format(x-args.box/2.0) + '\t{}'.format(y-args.box/2.0) + '\t{}'.format(args.box) * 2 + '\n')
						o_write.write('\n')
					if args.box != -1:
						o_box_write.close()
		# else it is before the particle extraction step, so you must want to convert star to box
		elif args.box != -1:
			basename = os.path.basename(os.path.splitext(star)[0])
			with open(star) as s_read:
				lines = s_read.readlines()[header_len:-1]
				with open(basename+'.box', 'w') as o_box_write:
					for line in lines:
						line = line.split()
						# get old coord
						x, y = float(line[star_dict['_rlnCoordinateX']]), float(line[star_dict['_rlnCoordinateY']])
						# exclude the edge
						if args.edge != -1:
							if not args.edge<=x<=args.x-args.edge or not args.edge<=y<=args.y-args.edge:
								continue
						o_box_write.write('{}'.format(x-args.box/2.0) + '\t{}'.format(y-args.box/2.0) + '\t{}'.format(args.box) * 2 + '\n')
			
if __name__ == '__main__':
	main()
