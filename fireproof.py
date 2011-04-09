#!/usr/bin/env python

import optparse

import jinja2

VERSION = '0.0.0'

def main():
    parser = optparse.OptionParser(usage="%prog [options]", version="%prog " + VERSION)
    
    (options, args) = parser.parse_args()

if __name__ == '__main__':
    main()
