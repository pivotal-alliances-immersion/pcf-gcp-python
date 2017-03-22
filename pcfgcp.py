import json
import os
from operator import itemgetter
import base64

from google.cloud import language
from google.cloud import vision
from google.cloud.vision.image import Image
from google.oauth2.service_account import Credentials

"""Base class for accessing Google Cloud Platform services from Python apps
deployed to PCF.  This class implements the authentication part.

Here are the various service names, as defined in

  https://github.com/GoogleCloudPlatform/gcp-service-broker/blob/master/brokerapi/brokers/models/service_broker.go

const StorageName = "google-storage"
const BigqueryName = "google-bigquery"
const BigtableName = "google-bigtable"
const CloudsqlName = "google-cloudsql"
const PubsubName = "google-pubsub"
const MlName = "google-ml-apis"

"""
class PcfGcp:
  def __init__(self):
    self.VCAP_SERVICES = None
    self.clients = {
      'google-storage': None
      , 'google-bigquery': None
      , 'google-bigtable': None
      , 'google-cloudsql': None
      , 'google-pubsub': None
      , 'language': None
      , 'vision': None
    }
    self.projectId = None
    self.bucketName = None # Storage

  def className(self):
    return self.__class__.__name__

  def getClient(self, name):
    return self.clients.get(name)

  def setClient(self, name, val):
    self.clients[name] = val

  def get_service_instance_dict(self, serviceName): # 'google-storage', etc.
    vcapStr = os.environ.get('VCAP_SERVICES')
    if vcapStr is None:
      raise Exception('VCAP_SERVICES not found in environment variables (necessary for credentials)')
    vcap = json.loads(vcapStr)
    svcs = None
    try:
      svcs = vcap[serviceName][0]
    except:
      raise Exception('No instance of ' + serviceName + ' available')
    return svcs

  """serviceName is one of the keys in clients
  """
  def get_google_cloud_credentials(self, serviceName):
    """Returns oauth2 credentials of type
    google.oauth2.service_account.Credentials
    """
    service_info = self.get_service_instance_dict(serviceName)
    pkey_data = base64.decodestring(service_info['credentials']['PrivateKeyData'])
    pkey_dict = json.loads(pkey_data)
    self.credentials = Credentials.from_service_account_info(pkey_dict)
    # Get additional fields
    self.projectId = service_info['credentials']['ProjectId']
    if 'bucket_name' in service_info['credentials']:
      self.bucketName = service_info['credentials']['bucket_name']
    return self.credentials

  """This can't be generic since the Client varies across services"""
  def getClient(self, serviceName):
    if self.clients[serviceName] is None:
      self.clients[serviceName] = language.Client(self.get_google_cloud_credentials(serviceName))
    return self.clients[serviceName]

  """Ref. https://cloud.google.com/natural-language/docs/sentiment-tutorial

    score ranges from -1.0 to 1.0
    magnitude ranges from 0.0 to Infinite (depends on length of document)

  """

  def getLanguage(self):
    if self.clients['language'] is None:
      self.clients['language'] = language.Client(self.get_google_cloud_credentials('google-ml-apis'))
    #print 'projectId: %s' % self.projectId
    return self.clients['language']

  """Ref. https://cloud.google.com/vision/docs/reference/libraries#client-libraries-install-python"""
  def getVision(self):
    if self.clients['vision'] is None:
      self.clients['vision'] = vision.Client(project=self.projectId,
        credentials=self.get_google_cloud_credentials('google-ml-apis'))
    return self.clients['vision']

  def getStorage(self):
    pass

  def getBigQuery(self):
    pass

  def getBigtable(self):
    pass

  def getCloudSql(self):
    pass

  def getPubSub(self):
    pass

