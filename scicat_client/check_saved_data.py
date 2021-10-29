import client
import os
from pprint import pprint


if __name__ == "__main__":

    import argparse
    from pprint import pprint
    import sys

    parser = argparse.ArgumentParser(usage="This is a test")
    parser.add_argument("pgroup", type=str, help="boh")
    parser.add_argument("datadir", type=str, help="boh")
    parser.add_argument("filelist", type=str, help="boh")

    args = parser.parse_args()

    filelist = args.filelist
    pgroup = args.pgroup
    datadir = args.datadir

    #includes = [".h5"]
    
    # raw
    scicat_files = {}
    with open(filelist) as f:
        for line in f:
            line = line.replace("//", "/")
            scicat_files[line.strip("\n")] = 1

    unsaved_files = []
    
    for dirpath, dirnames, filenames in os.walk(os.path.join(datadir, "raw")):
        for f in filenames:
            full_f = os.path.join(dirpath, f)
            full_f = full_f.replace("//", "/")
            proceed = False
            
            if full_f in scicat_files:
                _ = scicat_files.pop(full_f)
            else:
                unsaved_files.append(full_f)
                
    for dirpath, dirnames, filenames in os.walk(os.path.join(datadir, "res")):
        for f in filenames:
            full_f = os.path.join(dirpath, f)
            proceed = False
            
            if full_f in scicat_files:
                _ = scicat_files.pop(full_f)
            else:
                unsaved_files.append(full_f)

        
    for f in unsaved_files:
        print(f)
    
    
    
    
    
