import requests
import json
import getpass
import os
import logging
import urllib
import pprint


logger = logging.basicConfig()


class ScicatClient(object):

    def __init__(self, url):
        self.url = url

    def check_error(self, req):
        if req.status_code != requests.codes["ok"]:
            raise RuntimeError("Got error {} from {}: {}".format(req.status_code, self.url, req.reason))


    def get_token(self, user=None, token_file=None):
        if not token_file:
            token_file = os.path.join(os.getenv("HOME"), ".scicat_token")
        if os.path.isfile(token_file):
                with open(token_file) as f:
                    try:
                        token_json = json.loads(f.read().replace("'", "\""))
                        self.token = token_json["access_token"]
                    except:
                        raise ValueError("File {} does not contain a valid token.".format(token_file))
                    return

        passwd  = getpass.getpass("Please provide password for user {}: ".format(user))
        req = requests.post("https://dacat.psi.ch/auth/msad", json={"username":user, "password":passwd})
        
        if req.status_code != requests.codes['ok']:
            raise RuntimeError("Request returned error {}: {}".format(req.status_code, req.reason))
        res = json.loads(req.content)

        self.token = res["access_token"]
        with open(token_file, "w") as f:
            f.write(str(res))

    def list_datasets(self, datasets=None):
        req = requests.get(self.url + "/Datasets", params={"access_token": self.token})
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
    sub_list.add_argument("-f", "--full", type=bool, help="full format")
    

    args = parser.parse_args()
    #parser.print_help()

    #print(args)

    user = os.getenv("USER")
    client = ScicatClient("https://dacat.psi.ch/api/v3")
    client.get_token(user=user)

    output_fields = ["creationTime", "creationLocation", "datasetName"]
    output_fields_long = output_fields
    if args.action == "list":
        datasets = client.list_datasets()
        #print(datasets)
        if args.full:
            pprint(datasets)
        elif args.long:
            #print("\t".join(len(output_fields) * ["{:25}", ]).format(*output_fields))
            for dst in datasets:
                try:
                    print("\t".join((len(output_fields) + 1) * ["{}", ]).format(*([dst[field] for field in output_fields]), dst["datasetlifecycle"]["retrievable"]))
                except:
                    print(sys.exc_info()[1])

        else:
            print("\t".join(len(output_fields) * ["{:25}", ]).format(*output_fields))
            for dst in datasets:
                print("\t".join(len(output_fields) * ["{}", ]).format(*[dst[field] for field in output_fields]))
    
    #for dataset in datasets:
    #    #print(dataset)
    #    #res = client.list_dataset_lifecycle(dataset["pid"])
    #    if dataset["datasetlifecycle"]["retrievable"]:
    #        print(dataset["datasetName"])