#!/usr/bin/env python

import optparse
import os

import jinja2

VERSION = '0.0.0'

def main():
    parser = optparse.OptionParser(usage="%prog [options] site_dir output_dir", version="%prog " + VERSION)
    
    (options, args) = parser.parse_args()
    
    if len(args) != 2:
        parser.error("incorrect number of arguments")
    
    site_dir   = os.path.abspath(args[0])
    output_dir = os.path.abspath(args[1])
    
    # Check that the site and output directories meet the requirements
    if not os.path.exists(site_dir):
        parser.error("site directory '%s' doesn't exist" % site_dir)
    if not os.path.isdir(site_dir):
        parser.error("site directory '%s' isn't a directory" % site_dir)
    if os.path.exists(output_dir) and not os.path.isdir(output_dir):
        parser.error("output directory '%s' isn't a directory" % output_dir)
    if os.path.isdir(output_dir) and len(os.listdir(output_dir)) != 0:
        parser.error("output directory '%s' must be empty" % output_dir)

if __name__ == '__main__':
    main()
