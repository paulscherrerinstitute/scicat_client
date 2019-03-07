import requests
import json
import getpass
import os
import logging
import urllib
import pprint


logger = logging.getLogger('spam_application')


class ScicatClient(object):

    def __init__(self, url):
        self.url = url
        self.token_file = os.path.join(os.getenv("HOME"), ".scicat_token")

    def check_error(self, req):
        if req.status_code != requests.codes["ok"]:
            raise RuntimeError("Got error {} from {}: {}".format(req.status_code, self.url, req.reason))


    def get_token(self, user=None, token_file=None):
        if not token_file:
            token_file = self.token_file

        if os.path.isfile(token_file):
                with open(token_file) as f:
                    try:
                        token_json = json.loads(f.read().replace("'", "\""))
                        self.token = token_json["access_token"]
                    except:
                        raise ValueError("File {} does not contain a valid token.".format(token_file))

                # Basic token validity check                
                """req = requests.get(self.url + "/Datasets/count")
                print(req)
                if req.status_code == 401:
                    logger.warning("Token expired, removing token file and trying again")
                    os.unlink(token_file)
                    self.get_token(user=user, token_file=token_file)
                    return
                else:
                    self.check_error(req)
                """
                return

        passwd  = getpass.getpass("Please provide password for user {}: ".format(user))
        req = requests.post("https://dacat.psi.ch/auth/msad", json={"username":user, "password":passwd})
        
        if req.status_code != requests.codes['ok']:
            raise RuntimeError("Request returned error {}: {}".format(req.status_code, req.reason))
        res = json.loads(req.content)

        self.token = res["access_token"]
        with open(token_file, "w") as f:
            f.write(str(res))
        return

    def list_datasets(self, datasets=None, filters=None):
        params = {"access_token": self.token}
        # does not work???
        # Datasets?filter={"filter":{"ownerGroup":"p17502"}}&access_token=
        if filters is not None:
            if isinstance(filters, dict):
                params["filter"] = json.dumps({"filter":filters})

        req = requests.get(self.url + "/Datasets", params=params)
        print(dir(req), req.url)
        self.check_error(req)
        #print(req)
        #print(req.url)
        res = json.loads(req.content)
        #print(res)
        #for item in sorted(res, key=lambda x: x["createdAt"]):
            #print(item["pid"], item["createdAt"], item["ownerGroup"], item["datasetName"])
        #    pprint.pprint(item)
        return res

    def list_dataset_lifecycle(self, dataset_id):
        req = requests.get(self.url + "/Datasets/{}/datasetlifecycle".format(urllib.parse.quote(dataset_id, safe="")), params={"access_token": self.token})
        res = json.loads(req.content)
        return res


if __name__ == "__main__":

    import argparse
    from pprint import pprint
    import sys

    parser = argparse.ArgumentParser(usage="This is a test")

    #parser.add_argument("action", type=str, help="boh", choices=["list", ])
    subparsers = parser.add_subparsers(dest="action")

    sub_list = subparsers.add_parser("list")
    sub_list.add_argument("-l", "--long", action="store_true", help="long format")
    sub_list.add_argument("-f", "--full", action="store_true", help="full format")
    sub_list.add_argument("-d", "--dataset", type=str, help="NOT IMPLEMENTED dataset id")
    sub_list.add_argument("-s", "--search", type=str, help="search by dataset name", default=None)
    #sub_list.add_argument("--filter", action=str, help="filters, in 'key=value,key=value' format")
    
    sub_dump = subparsers.add_parser("dump_filelist")
    sub_list.add_argument("-g", "--group", type=str, help="Owner group")


    args = parser.parse_args()

    user = os.getenv("USER")
    client = ScicatClient("https://dacat.psi.ch/api/v3")
    client.get_token(user=user)

    output_fields = ["creationTime", "creationLocation", "size", "datasetName"]
    output_fields_long = output_fields
    if args.action == "list":
        datasets = client.list_datasets()

        for dst in datasets:
            if "creationLocation" not in dst.keys():
                continue
            if args.search is not None:
                if dst["datasetName"].find(args.search) == -1:
                    continue
            if args.full:
                pprint(dst)
            elif args.long:
                try:
                    print("\t".join((len(output_fields) + 1) * ["{}", ]).format(*([dst[field] for field in output_fields[:-1]]), dst["datasetlifecycle"]["retrievable"], dst["datasetName"]))
                except:
                    print(sys.exc_info()[1])

            else:
                try:
                    print("\t".join(len(output_fields) * ["{}", ]).format(*[dst[field] for field in output_fields]))
                except:
                    print(sys.exc_info()[1])

    elif args.action == "dump_filelist":
        datasets = client.list_datasets(filters={"ownerGroup":"p17502"})
        for dataset in datasets:
            pprint(dataset["ownerGroup"] + " " + dataset["datasetName"])
