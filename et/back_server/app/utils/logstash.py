import logging
import logstash
import sys

class MyLogstashFormatter(LogstashFormatterBase):
 
    def __init__(self, message_type='Logstash', tags=None, fqdn=False, status=None):
        super(MyLogstashFormatter, self).__init__(message_type, tags, fqdn)
        self.status = status if status else {}
 
    def format(self, record):
        message = {
            '@timestamp': self.format_timestamp(record.created),
            '@version': '1',
            'message': self.format_exception(record.exc_info) if self.format_exception(
                record.exc_info) else record.getMessage(),
            'host': local_ip,
            'hostId': HOST_ID,
            'path': '[line:{}]{}'.format(record.lineno, record.pathname),
            'tags': self.tags,
            'process': record.processName,
            'msgType': self.message_type,
            'app': 'api/' + env,
 
            # Extra Fields
            'level': record.levelname,
            'logger_name': self.host,
        }
        # Add extra fields
        message.update(self.get_extra_fields(record))
        
        # delete random item if length of status over 1000
        [self.status.popitem() for i in range(len(self.status)-1000) if len(self.status) >= 1000]
        return self.serialize(message)
 
 
class LogHandler(TCPLogstashHandler):
 
    def __init__(self, host, port, message_type='flask', tags=None, fqdn=False, version=0):
        super(LogHandler, self).__init__(host, port, message_type, tags, fqdn, version)
        self.formatter = MyLogstashFormatter(message_type, tags, fqdn)
 
 
def init(app):
    app.logger.addHandler(LogHandler(LOG_STASH_HOST, LOG_STASH_PORT, tags=''))