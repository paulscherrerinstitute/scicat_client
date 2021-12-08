from . import client
import os
from pprint import pprint
import io
import sys


def cli():
    import argparse
    from pprint import pprint
    import sys

    parser = argparse.ArgumentParser(usage="Check whether data in a directory is present in the Scicat archived data")
    parser.add_argument("pgroup", type=str, help="boh")
    parser.add_argument("datadir", type=str, help="boh")
    parser.add_argument("-o", "--output-file", type=str, help="Output file, default: filelist_notsaved.txt", default="filelist_notsavedh5.txt")
    # parser.add_argument("filelist", type=str, help="boh")

    args = parser.parse_args()

    # filelist = args.filelist
    pgroup = args.pgroup
    datadir = args.datadir
    output_file = args.output_file

    #includes = [".h5"]
    
    # redirect output to list
    orig_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout    # f = 
    # sys.stdout = f
    client.cli(["dump_filelist", "-g", pgroup])
    output = new_stdout.getvalue().split("\n")
    sys.stdout = orig_stdout

    #rint(output)
    scicat_files = {}
    # with open(filelist) as f:
    for line in output:
        line = line.replace("//", "/")
        scicat_files[line.strip("\n").strip(" ")] = 1

    unsaved_files = []
    
    for dirpath, dirnames, filenames in os.walk(datadir):
        for f in filenames:
            full_f = os.path.join(dirpath, f)
            full_f = full_f.replace("//", "/")
            proceed = False

            if full_f in scicat_files:
                _ = scicat_files.pop(full_f)
            else:
                unsaved_files.append(full_f)

    if len(unsaved_files) == 0:
        print(f"There are no files in {datadir} that are not archived")
    else:
        print(f"{len(unsaved_files)} files in {datadir} are not archived, see {output_file}")
        with open(output_file, "w") as f:
            for line in unsaved_files:
                f.write(line + "\n")
    
    
    
if __name__ == "__main__":
    cli()    
    
