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
formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)


class ScicatClient(object):

    instances = {"prod": "https://dacat.psi.ch/", "qa": "https://dacat-qa.psi.ch/"}
    version = "api/v3"
    max_auth_tries = 3
    current_auth_try = 0

    def __init__(self, instance="prod", user=None, token_file=None):
        """Initializes the ScicatClient class
        
        Parameters
        ----------
        instance : str, optional
            which SciCat instance to use, by default "prod"
        user : str, optional
            specify the user, by default it is retrieved from the environment variables
        token_file : str, optional
            specify the file containing the token and user it, by default ~/.scicat_token[_qa]
        """
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
        """Simple routine to check requests errors
        
        Parameters
        ----------
        req : object
            request object from requests
        
        Raises
        ------
        RuntimeError
        """
        logger.debug(req.status_code, req.reason, req.content)
        if req.status_code != requests.codes["ok"]:
            if req.status_code == 401:
                self.get_token(overwrite=True)
            else:
                logger.error("query {}".format(req.url))
                raise RuntimeError("Got error {} from {}: {}".format(req.status_code, self.url, req.reason))

    def check_token(self):
        """Checks token validity against a test REST API call
        
        Returns
        -------
        bool
            True if the request is successful, false otherwise
        """

        params = {"access_token": self.token}
        req = requests.get(self.url + "/Users/{}".format(self.id), params=params)
        logger.debug(req.content)
        self.current_auth_try = 0
        logger.debug(req.ok)
        return req.ok

    def get_token(self, overwrite=False):
        """Get a token, or verify existing token. MAximum number of tries set by self.max_auth_tries
        
        Parameters
        ----------
        overwrite : bool, optional
            Overwrite existing token, by default False
        
        Returns
        -------
        Bool
            True if success, False otherwise
        
        """
        if os.path.isfile(self.token_file) and not overwrite:
            logger.info("Reading token from {}".format(self.token_file))
            with open(self.token_file) as f:
                try:
                    token_json = json.loads(f.read().replace("'", "\""))
                    self.token = token_json["access_token"]
                    self.id = token_json["userId"]
                except:
                    logger.error(sys.exc_info())
                    raise ValueError("File {} does not contain a valid json-formatted token.".format(self.token_file))
            if self.check_token():
                logger.debug(self.token)
                logger.info("Found a valid token in {}".format(self.token_file))
                return True
            else:
                logger.info("Invalid or expired token in {}, regenerating".format(self.token_file))

        if self.current_auth_try > self.max_auth_tries:
            raise RuntimeError("Cannot get a valid token, please check your permissions")

        passwd  = getpass.getpass("Please provide password for user {}: ".format(self.user))
        logger.debug(self.instances[self.instance] + "/auth/msad")
        req = requests.post(self.instances[self.instance] + "auth/msad", json={"username":self.user, "password":passwd})
       
        if req.status_code != requests.codes['ok']:
            raise RuntimeError("Request returned error {}: {}".format(req.status_code, req.reason))
        res = json.loads(req.content)

        self.token = res["access_token"]
        self.id = res["userId"]
        with open(self.token_file, "w") as f:
            f.write(str(res))
        self.current_auth_try += 1

        if not self.check_token():
            return False
        else:
            logger.info("Token saved in {}".format(self.token_file))
        return True

    def list_datasets(self, datasets=None, filters=None, order_field="creationTime", order="ASC", limit=-1):
        params = {"access_token": self.token}
        params["filter"] = {}
        params["filter"]["order"] = "{} {}".format(order_field, order)
        if limit != -1:
            params["filter"]["limit"] = limit
        # does not work???
        # Datasets?filter={"filter":{"ownerGroup":"p17502"}}&access_token=
        if filters is not None:
            params['filter']["where"] = json.loads(filters)
        
        params["filter"] = json.dumps(params["filter"])
        logger.debug(params)
        req = requests.get(self.url + "/Datasets", params=params, )
        self.check_error(req)
        logger.info(req.url)
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

    usage = """Simple python client for SciCat.

Examples:

* Get a list of the first 10 datasets ingested

python scicat_client.py list --limit 10

* Filter out results (more on the query language here https://github.com/strongloop/loopback-filters)

python scicat_client.py list --filter '{"and": [{"owner": {"eq": \"""" + os.getenv("USER") + """\"}}, {"datasetlifecycle.retrievable": true}]}'
    """
    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument("--instance", type=str, help="SciCat instance", choices=["prod", "qa"], default="prod")
    parser.add_argument("-v", "--verbose", action="store_true")


    #parser.add_argument("action", type=str, help="boh", choices=["list", ])
    subparsers = parser.add_subparsers(dest="action")

    sub_list = subparsers.add_parser("token", help="Generate a token")


    sub_list = subparsers.add_parser("list")
    sub_list.add_argument("--long", action="store_true", help="long format")
    sub_list.add_argument("--full", action="store_true", help="full format")
    sub_list.add_argument("-d", "--dataset", type=str, help="NOT IMPLEMENTED dataset id")
    sub_list.add_argument("-s", "--search", type=str, help="search by dataset name", default=None)
    sub_list.add_argument("--filter", type=str, help="filters, in 'key=value,key=value' format")
    sub_list.add_argument("--with-bad-datasets", action="store_true", help="report whether a dataset does not conform with the data model, e.g. it is old")
    sub_list.add_argument("--limit", type=int, help="Limit the number of results to X", default=-1)
    
    
    sub_dump = subparsers.add_parser("dump_filelist")
    sub_dump.add_argument("-g", "--group", type=str, help="Owner group")


    args = parser.parse_args()

    if args.verbose:
        logger.setLevel("DEBUG")
    else:
        logger.setLevel("INFO")

    if args.action is None:
        parser.print_help()
        sys.exit()

    client = ScicatClient(instance=args.instance)

    if not client.get_token():
        logger.error("Cannot get a valid token")
        sys.exit(1)

    if args.action == "token":
        sys.exit()


    output_fields = ["creationTime", "creationLocation", "size", "datasetName"]
    output_fields_long = output_fields[:-1] + ["owner", "datasetName"] 


    if args.action == "list":
        datasets = client.list_datasets(filters=args.filter, limit=args.limit)

        logger.debug(datasets)

        header = '\t'.join(output_fields)
        if args.long:
            tmp_fields = output_fields_long.copy()
            tmp_fields.insert(-1, "retrievable")
            header = '\t'.join(tmp_fields)
        print(header.upper())
        # this means something went wrong
        if isinstance(datasets, str) or "error" in datasets:
            raise RuntimeError(datasets)
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
                    print("\t".join((len(output_fields_long) + 1) * ["{}", ]).format(*([dst[field] for field in output_fields_long[:-1]]), dst["datasetlifecycle"]["retrievable"], dst["datasetName"]))
                except:
                    if args.with_bad_datasets:
                        logger.error("{} produced this error: {}".format(dst["datasetName"], sys.exc_info()))
            else:
                try:
                    print("\t".join(len(output_fields) * ["{}", ]).format(*[dst[field] for field in output_fields]))
                except:
                    if args.with_bad_datasets:
                        logger.error("{} produced this error: {}".format(dst["datasetName"], sys.exc_info()))
    
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