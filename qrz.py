import json
import requests
import xmltodict

class QRZ:
    def __init__(self,logbook):
        with open(f"{logbook}_config.json") as config:
            log_config = json.load(config)
            self.api_key = log_config.get("key")
            self.api_endpoint = log_config.get("endpoint")
            self.qrz_username =  log_config.get("qrz_username")
            self.qrz_password = log_config.get("qrz_password")
            self.qrz_call_endpoint = log_config.get("qrz_call_endpoint")
            self.qrz_session_key = None

    def post_adif_log(self,adif):
        data = {
            "KEY": self.api_key,
            "ACTION": "INSERT",
            "ADIF": adif.strip()
        }

        r = requests.post(self.api_endpoint,data=data)
        return r.status_code

    def qrz_xml_response_parse(self,xmltext):
        xml = "".join(xmltext.split('\n')[1:]) # Strip the first line of the response.
        return xmltodict.parse(xml).get("QRZDatabase")
        

    def login(self):
        data = {"username":self.qrz_username,"password":self.qrz_password}
        r = requests.post(self.qrz_call_endpoint,data=data)
        if r.status_code == 200:
            qrz_dict = self.qrz_xml_response_parse(r.text)
            if qrz_dict and qrz_dict.get("Session"):
                self.qrz_session_key = qrz_dict["Session"]["Key"]
        else:
            raise Exception(f"QRZ.com XML api login failed with status code: {r.status_code}")
            
    def callsign_lookup(self,callsign):
        if not self.qrz_session_key:
            self.login()

        r = requests.get(f"{self.qrz_call_endpoint}?s={self.qrz_session_key};callsign={callsign}")
        if r.status_code == 200:
            qrz_dict = self.qrz_xml_response_parse(r.text)
            # If there is a session key in the response then parse the callsign lookup result
            if qrz_dict and qrz_dict.get("Session") and qrz_dict["Session"].get("Key"):
                return qrz_dict.get("Callsign")
            else:
                # Invalidate the local session.
                self.qrz_session_key = None
        else:
            raise Exception(f"QRZ.com callsign lookup failed with status code: {r.status_code}")



