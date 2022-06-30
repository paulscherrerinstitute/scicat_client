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
    parser.add_argument("pgroup", type=str, help="Name of the pgroup to analyze, e.g. pXXXXX")
    parser.add_argument("datadir", type=str, help="Directory to compare with tape, e.g. /sf/alvra/data/pXXXXX/raw")
    parser.add_argument("-o", "--output-file", type=str, help="Output file, default: filelist_notsaved.txt", default="filelist_notsavedh5.txt")
    parser.add_argument("--token", type=str, help="Scicat token. Please retrieve your user token here: https://discovery.psi.ch/user , field 'Catamel token'", default=None)

    args = parser.parse_args()

    pgroup = args.pgroup
    datadir = args.datadir
    output_file = args.output_file
    check_saved_data(pgroup, datadir, output_file, args.token)
    


def check_saved_data(pgroup, datadir, outputfile, token):

    #includes = [".h5"]
    files_on_tape_fname = f"{pgroup}_ontape.txt"
    files_on_disk_fname = f"{pgroup}_ondisk.txt"

    # redirect output to list
    orig_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout    # f = 
    #sys.stdout = f
    ret = client.cli(["--token", token, "dump_filelist", "-g", pgroup])
    output = new_stdout.getvalue().split("\n")
    #print(output)
    sys.stdout = orig_stdout
    if ret != 0:
        print('\n'.join(output))
        return 1

    #rint(output)
    scicat_files = {}
    with open(files_on_tape_fname, "w") as f:
        for line in output:
            line = line.replace("//", "/")
            f.write(line + '\n')
            scicat_files[line.strip("\n").strip(" ")] = 1

    files_on_tape = len(scicat_files)

    unsaved_files = []
    
    files_on_disk = 0
    with open(files_on_disk_fname, "w") as f:
        for dirpath, dirnames, filenames in os.walk(datadir):
            for fname in filenames:
                full_f = os.path.join(dirpath, fname)
                full_f = full_f.replace("//", "/")
                f.write(full_f + '\n')
                proceed = False
                
                files_on_disk += 1

                if full_f in scicat_files:
                    _ = scicat_files.pop(full_f)
                else:
                    unsaved_files.append(full_f)
                
    print(f"Files on disk analyzed: {files_on_disk}")
    print(f"Files on tape analyzed: {files_on_tape}")

    if len(unsaved_files) == 0:
        print(f"There are no files in {datadir} that are not archived")
    else:
        print(f"{len(unsaved_files)} files in {datadir} are not archived, see {outputfile}")
        with open(outputfile, "w") as f:
            for line in unsaved_files:
                f.write(line + "\n")
    print(f"List of all files on disk is reported here: {files_on_disk_fname}")
    print(f"List of all files on tape archive is reported here: {files_on_tape_fname}")
    return 0
    
    
if __name__ == "__main__":
    ret = cli()    
    sys.exit(ret)
