import slumber
import os
import urllib2
import json
from slumber.exceptions import HttpClientError
from requests.auth import AuthBase
from random import randint
from ConfigParser import RawConfigParser
from time import sleep
from logger import Logger


CONFIG_ENCODING = 'utf-8'
YATANKAPI_PORT = '8888'
log = Logger.get_logger()


class DRFApikeyAuth(AuthBase):
    def __init__(self, apikey):
        self.apikey = apikey

    def __call__(self, r):
        r.headers['Authorization'] = "Token {0}".format(self.apikey)
        return r


class SaltsApiException(Exception):
    pass


class SaltsClient(slumber.API):

    file_fields = ['metrics', 'jm_log', 'modified_jmx',
                   'ph_conf', 'yt_conf', 'yt_log',
                   'console_log', 'report_txt', 'jm_jtl',
                   'phout', 'jm_log_2']

    SECTION = 'salts'
    POLL_INTERVAL = 5

    def __init__(self, base_url, apikey, repo_path=None):
        slumber.API.__init__(self, base_url=base_url,
                             auth=DRFApikeyAuth(apikey))
        self.repo_path = repo_path
        self.user_name = ''
        self.git_scenario_path = ''
        try:
            self.generatortype.get()
        except Exception:
            raise SaltsApiException("Authentication failed on %s: "
                                    "please check token. "
                                    "'%s' token given." % (base_url, apikey))

    def shoot(self, scenario_id, tank_param=('localhost', 8888),
              replacement='', wait_for_finish=True):
        from urllib import quote_plus
        from urlparse import urlparse
        try:
            base_url_obj = urlparse(self._store.get('base_url'))
            (tank_host, tank_port) = tank_param
            tank = self.tank.get(host=tank_host, port=tank_port)
            if not tank:
                raise SaltsApiException("Invalid tank parameters are given")
            url = "%s://%s/shoot?s=%s&t=%s&j=%s" \
                  % (base_url_obj.scheme, base_url_obj.netloc,
                     scenario_id, tank[0]['id'],
                     quote_plus(replacement.encode('base64', 'strict')))
            f = urllib2.urlopen(url)
            log.info("The shooting has been started.")
            response = json.loads(f.read())
            while True:
                sleep(SaltsClient.POLL_INTERVAL)
                shooting = self.shooting.get(id=response['id'],
                                             random=randint(1, 1000000))[0]
                log.info("shooting_id: %s; session_id: %s; status: %s" \
                         % (shooting['id'], shooting['session_id'],
                            shooting['status']))
                if shooting['status'] in ['F', 'I']:
                    break
        except HttpClientError, exc:
            raise SaltsApiException("Start Test HTTP Error: %s. "
                                    "Content: %s." % (exc, exc.content))
        except Exception, exc:
            raise SaltsApiException("Start Test Error: %s." % exc)

    def test_result(self, session_id):
        result = self.testresult.get(
                        session_id=session_id,
                        random=randint(1, 1000000)
                    )
        if result:
            return result[0]
        return result

    def save_test_result(self, **kwargs):
        gen_types = []
        if "generator_types" in kwargs:
            gen_types = kwargs["generator_types"]
        try:
            gen_type_objects = [self.generatortype.get(name=gt)[0]
                                for gt in gen_types]
            data = {"session_id": kwargs["session_id"],
                    "scenario_path": kwargs["scenario_path"],
                    "dt_start": kwargs["dt_start"],
                    "dt_finish": kwargs["dt_finish"],
                    "group": (kwargs["group"] or "").decode(CONFIG_ENCODING)[:32],
                    "test_name": (kwargs["test_name"] or "").decode(CONFIG_ENCODING)[:128],
                    "target":  kwargs["target"].decode(CONFIG_ENCODING)[:128],
                    "version":  (kwargs["version"] or "").decode(CONFIG_ENCODING)[:128],
                    "rps":  kwargs["rps"].decode(CONFIG_ENCODING)[:128],
                    "q99":  kwargs["q99"],
                    "q90":  kwargs["q90"],
                    "q50":  kwargs["q50"],
                    "http_errors_perc":  kwargs["http_errors_perc"],
                    "net_errors_perc":  kwargs["net_errors_perc"],
                    "graph_url":  kwargs["graph_url"].decode(CONFIG_ENCODING)[:256],
                    "generator":  kwargs["generator"].decode(CONFIG_ENCODING)[:128],
                    "user":  kwargs["user"].decode(CONFIG_ENCODING)[:128],
                    "ticket_id":  (kwargs["ticket_id"] or "").decode(CONFIG_ENCODING)[:64],
                    "mnt_url":  (kwargs["mnt_url"] or "").decode(CONFIG_ENCODING)[:256],
                    "comments": kwargs["comments"],
                    "generator_types": gen_type_objects,
                    "test_status": kwargs["test_status"]}
            res = self.testresult.post(data)
            return res
        except HttpClientError, exc:
            raise SaltsApiException("Save TestResult HTTP Error: %s. "
                                    "Content: %s." % (exc, exc.content))
        except Exception, exc:
            raise SaltsApiException("Error sending results to salts: %s" % exc)

    def update_test_result(self, id, **kwargs):
        kv = kwargs.copy()
        files = {}
        try:
            for field in kwargs:
                if field in self.file_fields:
                    files[field] = open(kwargs[field])
                    del kv[field]
            if files:
                self.testresult(id).put(files=files)
                for field in files:
                    files[field].close()
        except HttpClientError, exc:
            raise SaltsApiException("Update TestResult HTTP Error: %s. "
                                    "Content: %s." % (exc, exc.content))
        except Exception, exc:
            raise SaltsApiException("Error sending artifact "
                                    "file to salts: %s" % exc)
        if kv:
            try:
                self.testresult(id).put(kv)
            except HttpClientError, exc:
                raise SaltsApiException("Update TestResult HTTP Error: %s. "
                                        "Content: %s." % (exc, exc.content))
            except Exception, exc:
                raise SaltsApiException("Error update fields "
                                        "to salts: %s" % exc)

    def update_shooting(self, session_id, **kwargs):
        try:
            shooting = self.shooting.get(session_id=session_id,
                                         random=randint(1, 1000000))
            if shooting:
                shooting = shooting[0]
                if kwargs.get('status') and shooting['status'] in ['I', 'F']:
                    kwargs.pop('status')
                if not kwargs:
                    return
                req_fields = {'tank': shooting['tank'],
                              'scenario': shooting['scenario']}
                updated_data = dict(req_fields.items() + kwargs.items())
                p = self.shooting(shooting['id']).put(updated_data)
            else:
                scenario_id = kwargs.get('scenario_id')
                if not scenario_id:
                    raise SaltsApiException(
                            "Shooting Update: scenario_id is required")
                scenario = self.scenario.get(id=scenario_id)
                if not scenario:
                    raise SaltsApiException(
                            "Unknown scenario_id: %s" % scenario_id)
                scenario = scenario[0]
                tank_param = (kwargs.get('tank_host'), YATANKAPI_PORT)
                tank = self.tank.get(host=tank_param[0],
                                    port=tank_param[1])
                if not tank:
                    raise SaltsApiException(
                            "Unknown tank host %s or port %s" % tank_param)
                tank = tank[0]
                req_fields = {'session_id': session_id,
                              'tank': tank['url'],
                              'scenario': scenario['url']}
                post_data = dict(req_fields.items() + kwargs.items())
                shooting = self.shooting.post(post_data)
                self.git_scenario_path = scenario['scenario_path']
        except HttpClientError, exc:
            raise SaltsApiException("SaltsClient HTTP Error: %s. "
                                    "Content: %s." % (exc, exc.content))
        except Exception, exc:
            log.warning("SaltsClient Exception: %s" % exc)
            raise SaltsApiException(exc)

        self.user_name = shooting['alt_name']

    def provide_scenario_id(self, scenario_path):
        scenario = self.scenario.get(scenario_path=scenario_path)
        if scenario:
            return scenario[0]['id']
        group = self.group.get(name='Salts')
        post_data = {'scenario_path': scenario_path,
                     'group': group[0]['url']}
        try:
            scenario = self.scenario.post(post_data)
            return scenario['id']
        except Exception, exc:
            log.warning("SaltsClient Exception: %s" % exc)
            raise SaltsApiException(exc)

    def get_user_name(self):
        if not self.user_name:
            log.warning("User name is empty. "
                        "It should be defined after prepare_test stage.")
        return self.user_name

    def get_git_scenario_path(self):
        if not self.git_scenario_path:
            log.warning("Git scenario path is empty. "
                        "It should be defined after prepare_test stage.")
        return self.git_scenario_path
