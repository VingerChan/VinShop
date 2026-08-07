from django.conf import settings
from elasticsearch import Elasticsearch

# 第一次调用才真正创建，之后所有地方复用同一个client
_client = None
def get_client():
    global _client
    if _client is None:
        _client = Elasticsearch(hosts=[settings.ES_HOST],request_timeout=30)
    return _client