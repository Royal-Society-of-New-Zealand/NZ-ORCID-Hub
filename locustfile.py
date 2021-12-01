import random
import secrets
import logging

import urllib3

# Create the _locustfile.py from _locustfile.sample.py
try:
    from _locustfile import password, username
except:
    print("*** Create the _locustfile.py from _locustfile.sample.py")
    raise

# from locust import events, HttpUser, between, task
from locust import HttpUser, between, task

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class QuickstartUser(HttpUser):

    org_id = None
    org_name = None
    wait_time = between(5, 9)

    def on_start(self):
        self.client.verify = False
        self.login0()
        # self.login()
        # self.add_orgs()

    def add_orgs(self, n=10):
        for _ in range(10):
            self.add_org(secrets.token_hex(8))

    def on_stop(self):
        # self.logout()
        pass

    def login0(self):
        self.client.get(
            "/login0/",
            headers={
                "Authorization": f"{username}:{password}",
            },
        )

    def login(self):
        # resp = self.client.get("/accounts/login/")
        resp = self.client.get("/api-auth/login/")
        csrftoken = resp.cookies["csrftoken"]
        self.client.post(
            "/api-auth/login/",
            {"login": username, "password": password},
            headers={
                "X-CSRFToken": csrftoken,
                "Referer": self.client.base_url + "/api-auth/login/",
            },
        )

    def logout(self):
        # /accounts/logout/
        resp = self.client.get("/api-auth/logout/")
        csrftoken = resp.cookies["csrftoken"]
        self.client.post(
            "/api-auth/logout/",
            {"csrfmiddlewaretoken": csrftoken},
            headers={
                "X-CSRFToken": csrftoken,
                "Referer": self.client.base_url + "/api-auth/logout/",
            },
        )

    @task(5)
    def home(self):
        self.client.get("/")

    @task(3)
    def members(self):
        self.client.get("/admin/viewmembers/")

    @task(3)
    def orginfo(self):
        self.client.get("/admin/orginfo/")

    @task(3)
    def orginfo(self):
        self.client.get("/user_summary/", allow_redirects=True)

    @task
    def profile(self):
        self.client.get("/profile")

    # @property
    # def last_transaction_id(self):
    #     resp = self.client.get(
    #         "/api/v1/itsl/transactions/?ordering=-id&limit=1", auth=(username, password)
    #     )

    #     data = resp.json()
    #     if not data["count"]:
    #         return 1
    #     last_id = data["results"][0]["id"]
    #     # logging.info(f"*** last_id: {last_id}")
    #     return last_id

    # def send_transations(self):
    #     last_id = self.last_transaction_id
    #     resp = self.client.post(
    #         "/api/v1/itsl/transactions/",
    #         # data=f"{last_id+1},ABCD1234-NZ,Cash,Sale,Approved,123,1.00,2021-04-26 12:26:13 +10:00,2021-05-26 16:55:34 +10:00,ABC12345,Visa,1234,CODE19",
    #         auth=(username, password),
    #         headers={"Content-Type": "text/plain"},
    #         data="\r\n".join(
    #             f"{id},ABCD{id/42 + 12345}-NZ,Cash,Sale,Approved,123,1.00,2021-04-26 12:26:13 +10:00,2021-05-26 16:55:34 +10:00,ABC123,Visa,1234,CODE9"
    #             for id in range(last_id + 1, last_id + random.randint(100, 10000))
    #         ),
    #     )
    #     # logging.info(f"*** RESP: {resp.text}")

    def add_org(self, name):
        resp = self.client.get(f"/autocomplete/org/?q={name}")
        # breakpoint()
        if "create_id" in resp.json()["results"][0]:
            resp = self.client.get("/profile/employments/")
            csrftoken = resp.cookies["csrftoken"]
            resp = self.client.post(
                "/autocomplete/org/",
                {"text": name},
                headers={
                    "X-CSRFToken": csrftoken,
                    "Referer": self.client.base_url + "/profile/employments/",
                },
            )
            # breakpoint()
            resp = self.client.get(f"/autocomplete/org/?q={name}")
        self.org_id = resp.json()["results"][0]["id"]
        self.org_name = name

    # @task
    # def index_page(self):
    #     self.client.get("/")
    #     self.client.get("/index")
    #     self.client.get("/start")

    # @task
    # def view_profile(self):
    #     self.client.get("/profile/")

    # @task
    # def view_employment(self):
    #     self.client.get("/profile/employments/")

    def get_random_org_ids(self, k=7):
        while True:
            q = random.choice("0123456789abcdef")
            resp = self.client.get(f"/autocomplete/org/?q={q}")
            data = resp.json()
            org_ids = random.choices([d["id"] for d in data["results"] if d["id"].isdigit()], k=k)
            if org_ids:
                break
        return org_ids

    # @task
    def admin_organisations(self):
        self.client.get(f"/admin/portal/organisation/?p={random.randint(1,100)}")

    # @task
    def admin_organisations_add(self):
        resp = self.client.get("/admin/portal/organisation/add/")
        csrftoken = resp.cookies["csrftoken"]
        self.client.post(
            "/admin/portal/organisation/add/",
            dict(
                csrfmiddlewaretoken=csrftoken,
                name=f"TEST {secrets.token_hex(8)}",
                identifier_type="99",
                identifier=secrets.token_hex(7),
                code=secrets.token_hex(4),
            ),
            headers={
                "X-CSRFToken": csrftoken,
                "Referer": self.client.base_url + "/profile/employments/",
            },
        )

    def upate_employments(self):

        org_ids = self.get_random_org_ids()

        resp = self.client.get("/api/affiliations/")
        data = resp.json()
        affiliation_ids = [a["id"] for a in data]
        profile_id = data[0]["profile"]

        data = {
            "form-TOTAL_FORMS": 7,
            "form-INITIAL_FORMS": len(affiliation_ids),
            "save": "Save",
        }
        for idx, org_id in enumerate(org_ids):
            data.update(
                {
                    f"form-{idx}-profile": profile_id,
                    f"form-{idx}-org": org_id,
                    f"form-{idx}-type": "EMP",
                    f"form-{idx}-role": "ROLE",
                    f"form-{idx}-start_date": "2020-05-02",
                    f"form-{idx}-end_date": "",
                    f"form-{idx}-id": ""
                    if idx + 1 > len(affiliation_ids)
                    else affiliation_ids[idx],
                }
            )

        resp = self.client.get("/profile/employments/")
        csrftoken = resp.cookies["csrftoken"]
        resp = self.client.post(
            "/profile/employments/",
            data,
            headers={
                "X-CSRFToken": csrftoken,
                "Referer": self.client.base_url + "/profile/employments/" "/accounts/login/",
            },
        )


# def track_success(**kwargs):
#     print(kwargs)


# events.request_success += track_success
