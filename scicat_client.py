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
        req = requests.post("https://dacat-qa.psi.ch/auth/msad", json={"username":user, "password":passwd})
        
        if req.status_code != requests.codes['ok']:
            raise RuntimeError("Request returned error {}: {}".format(req.status_code, req.reason))
        res = json.loads(req.content)

        self.token = res["access_token"]
        with open(token_file, "w") as f:
            f.write(str(res))

    def list_datasets(self, datasets=None):
        req = requests.get(self.url + "/Datasets", params={"access_token": self.token})
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

    user = os.getenv("USER")
    client = ScicatClient("https://dacat-qa.psi.ch/api/v3")
    client.get_token(user=user)
    datasets = client.list_datasets()
    for dataset in datasets:
        #print(dataset)
        #res = client.list_dataset_lifecycle(dataset["pid"])
        if dataset["datasetlifecycle"]["retrievable"]:
            print(dataset["datasetName"])