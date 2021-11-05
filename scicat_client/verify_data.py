import client
import os
import scicat_client
import json
import sys
import argparse


def cli():
    parser = argparse.ArgumentParser(usage="A simple tool to verify archived data for a specific ownerGroup, based on file size")
    parser.add_argument("ownerGroup", type=str, help="Scicat Owner group to test")
    args = parser.parse_args()

    pgroup = args.pgroup

    client = client.ScicatClient()
    client.get_token()
    
    datasets = client.list_datasets(filters=json.dumps({'ownerGroup':args.pgroup}))

    errors = 0
    for dataset in datasets:
        blocks = client.list_dataset_blocks(dataset["pid"])
        for block in blocks:
            for f in block["dataFileList"]:
                if f["path"].find("__checksum_filename") == -1:
                    fname = os.path.join(dataset["sourceFolder"], f["path"])
                    fsize = os.stat(fname).st_size
                    if (fsize - f["size"]):
                        print(f"ERROR in {dataset} - {fname}: {f['size']} (archive) vs {fsize} (disk)")
                        errors += 1

    print(f"Found {errors} errors")


if __name__ == "__main__":
    cli()
    
