from keycloak import KeycloakOpenID
import requests
import json
import os
from model.Dtos import DataPoint

# Configure client
keycloak_openid = KeycloakOpenID(server_url= os.getenv("AUTHENTICATION_SERVER"),
                    client_id="odh-elaborations-lambda",
                    realm_name="noi",
                    client_secret_key=os.getenv("CLIENT_SECRET"),
                    verify=True)


class DataPusher:
    def pushData(self,stationType,stationCode,dataType,dataPoints):
        dataMap = self.createDataMap(stationCode,dataType,dataPoints)
        self.sendData(stationType,dataMap)

    def createDataMap(self,station,dataType,dataPoints):
        dataMap = {"name":"(default)","branch":{},"data": dataPoints}
        typeMap = {"name":"(default)","branch": {dataType:dataMap},"data":[]}
        stationMap = {"name":"(default)","branch":{station:typeMap},"data":[]}
        return stationMap

    def sendData(self,stationType, dataMap):
        token = keycloak_openid.token("", "","client_credentials")
        r = requests.post(os.getenv("ODH_SHARE_ENDPOINT")+"/json/pushRecords/"+stationType, json=dataMap, headers={"Authorization" : "Bearer " + token['access_token']})
        if (r.status_code != 201):
            print("Status code not 201 but " + str(r.status_code))
