# TODO sorted output

import requests
import json
import getpass
import os
import logging
import urllib
import pprint
import sys


logger = logging.getLogger('scicat client')
# create console handler with a higher log level
ch = logging.StreamHandler()
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)



class ScicatClient(object):

    instances = {"prod": "https://dacat.psi.ch/", "qa": "https://dacat-qa.psi.ch/"}
    version = "api/v3"

    def __init__(self, instance="prod", user=None, token_file=None):
        self.instance = instance
        self.url = self.instances[instance] + self.version
            
        if token_file is None:
            self.token_file = os.path.join(os.getenv("HOME"), ".scicat_token{}".format("" if instance == "prod" else "_{}".format(instance)))
        else:
            self.token_file = token_file
            
        if user is None:
            self.user = os.getenv("USER")
        else:
            self.user = user
        
    def check_error(self, req):
        logger.debug(req.status_code, req.reason, req.content)
        if req.status_code != requests.codes["ok"]:
            if req.status_code == 401:
                self.get_token(overwrite=True)
            else:
                logger.error("query {}".format(req.url))
                raise RuntimeError("Got error {} from {}: {}".format(req.status_code, self.url, req.reason))


    def get_token(self, overwrite=False):
        if os.path.isfile(self.token_file) and not overwrite:
            logger.info("Reading token from {}".format(self.token_file))
            with open(self.token_file) as f:
                try:
                    token_json = json.loads(f.read().replace("'", "\""))
                    self.token = token_json["access_token"]
                except:
                    logger.error(sys.exc_info())
                    raise ValueError("File {} does not contain a valid token.".format(self.token_file))
            return

        logger.debug(self.token)
        passwd  = getpass.getpass("Please provide password for user {}: ".format(self.user))
        logger.debug(self.instances[self.instance] + "/auth/msad")
        req = requests.post(self.instances[self.instance] + "auth/msad", json={"username":self.user, "password":passwd})
       
        if req.status_code != requests.codes['ok']:
            raise RuntimeError("Request returned error {}: {}".format(req.status_code, req.reason))
        res = json.loads(req.content)

        self.token = res["access_token"]
        with open(self.token_file, "w") as f:
            f.write(str(res))
        return

    def list_datasets(self, datasets=None, filters=None):
        params = {"access_token": self.token}
        # does not work???
        # Datasets?filter={"filter":{"ownerGroup":"p17502"}}&access_token=
        filters = {"datasetlifecycle": {"retrievable": True,}}
        if filters is not None:
            if isinstance(filters, dict):
                params['filter'] = json.dumps({"where":filters})
        req = requests.get(self.url + "/Datasets", params=params, )
        self.check_error(req)
        res = json.loads(req.content)
        return res

    def list_dataset_lifecycle(self, dataset_id):
        req = requests.get(self.url + "/Datasets/{}/datasetlifecycle".format(urllib.parse.quote(dataset_id, safe="")), params={"access_token": self.token})
        res = json.loads(req.content)
        return res

    def list_dataset_blocks(self, dataset_id):
        req = requests.get(self.url + "/Datasets/{}/datablocks".format(urllib.parse.quote(dataset_id, safe="")), params={"access_token": self.token})
        res = json.loads(req.content)
        return res

    
if __name__ == "__main__":

    import argparse
    from pprint import pprint
    import sys

    parser = argparse.ArgumentParser(usage="This is a test")
    parser.add_argument("--instance", type=str, help="SciCat instance", choices=["prod", "qa"], default="prod")

    logger.setLevel("DEBUG")

    #parser.add_argument("action", type=str, help="boh", choices=["list", ])
    subparsers = parser.add_subparsers(dest="action")

    sub_list = subparsers.add_parser("list")
    sub_list.add_argument("-l", "--long", action="store_true", help="long format")
    sub_list.add_argument("-f", "--full", action="store_true", help="full format")
    sub_list.add_argument("-d", "--dataset", type=str, help="NOT IMPLEMENTED dataset id")
    sub_list.add_argument("-s", "--search", type=str, help="search by dataset name", default=None)
    sub_list.add_argument("--filter", action="store_true", help="filters, in 'key=value,key=value' format")
    
    
    sub_dump = subparsers.add_parser("dump_filelist")
    sub_dump.add_argument("-g", "--group", type=str, help="Owner group")


    args = parser.parse_args()

    client = ScicatClient(instance=args.instance)
    client.get_token()

    output_fields = ["creationTime", "creationLocation", "size", "datasetName"]
    output_fields_long = output_fields

    if args.action == "list":
        datasets = client.list_datasets()  # filters=args.filter)

        logger.debug(datasets)
        for dst in datasets:
            # this is for old datasets, where there is no creation location field
            logger.debug("entry: {}".format(dst))
            if "creationLocation" not in dst.keys():
                dst["creationLocation"] = "-"
            # searching by dataset name
            if args.search is not None:
                if dst["datasetName"].find(args.search) == -1:
                    continue
            
            # select how to print
            if args.full:
                pprint(dst)
            elif args.long:
                try:
                    #pass
                    print("\t".join((len(output_fields) + 1) * ["{}", ]).format(*([dst[field] for field in output_fields[:-1]]), dst["datasetlifecycle"]["retrievable"], dst["datasetName"]))
                except:
                    print(dst)
                    print(sys.exc_info()[1])
            else:
                try:
                    print("\t".join(len(output_fields) * ["{}", ]).format(*[dst[field] for field in output_fields]))
                except:
                    print(sys.exc_info()[1])


    elif args.action == "dump_filelist":
        datasets = client.list_datasets(filters={'ownerGroup':args.group})
        for dataset in datasets:
            blocks = client.list_dataset_blocks(dataset["pid"])
            for block in blocks:
                for f in block["dataFileList"]:
                    if f["path"].find("__checksum_filename") == -1:
                        print(os.path.join(dataset["sourceFolder"], f["path"]))

    else:
        parser.print_help()