# -*- coding: utf-8 -*-
import smtplib
import socks
import re
from urllib.request import getproxies
from email.message import EmailMessage

from globals import CONFIG
import utils
# ============================================================= #

class Proxifier:

    def __init__(self, proxy_server=None, proxy_port=None, proxy_type='HTTP', proxy_username=None, proxy_password=None):
        self.proxy_type = {'HTTP': socks.HTTP, 'SOCKS4': socks.SOCKS4, 'SOCKS5': socks.SOCKS5}.get(proxy_type, socks.HTTP)
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        if not proxy_server or not proxy_port:
            self._get_sysproxy()
        else:
            self.proxy_server = proxy_server
            self.proxy_port = proxy_port        

    def _get_sysproxy(self, setvars=True):
        proxy_server, proxy_port, proxy_username, proxy_password = (None, None, None, None)
        template = re.compile(r'^(((?P<user>[^:]+)(:(?P<pass>[^@]*)?))@)?(?P<host>[^:]+?)(:(?P<port>\d{1,5})?)$', re.I)
        try:
            sys_proxy = getproxies()
            for p in sys_proxy:
                if p.lower().startswith('http') or p.lower().startswith('socks'):
                    sp = sys_proxy[p].split('//')
                    sp = sp[1] if len(sp) > 1 else sp[0]
                    m = template.fullmatch(sp)
                    proxy_server = m.group('host') or None
                    try:
                        proxy_port = int(m.group('port')) or None
                    except:
                        pass
                    proxy_username = m.group('user') or None
                    proxy_password = m.group('pass') or None
                    break
        except Exception as err:
            utils.log(err, how='exception')

        if setvars:
            self.proxy_server = proxy_server or self.proxy_server
            self.proxy_port = proxy_port or self.proxy_port
            self.proxy_username = proxy_username or self.proxy_username
            self.proxy_password = proxy_password or self.proxy_password
        return (proxy_server, proxy_port)

    def get_socket(self, source_address, host, port, timeout=None):
        return socks.create_connection((host, port), timeout, source_address, 
                                       proxy_type=self.proxy_type, proxy_addr=self.proxy_server, proxy_port=self.proxy_port, 
                                       proxy_username=self.proxy_username, proxy_password=self.proxy_password)

    @staticmethod
    def get_proxifier():
        proxy = CONFIG.get('proxy', None)
        if not proxy or not proxy.get('useproxy', False):
            return None
        return Proxifier(proxy.get('server', None), proxy.get('port', None), proxy.get('type', None), proxy.get('username', None), proxy.get('password', None))

# ============================================================= #                                       

class SMTP_Proxy(smtplib.SMTP):

    def __init__(self, host='', port=0, local_hostname=None, timeout=object(), source_address=None, 
                 proxifier: Proxifier=None):
        self._proxifier = proxifier
        super().__init__(host, port, local_hostname, timeout, source_address)        

    def _get_socket(self, host, port, timeout):
        if not self._proxifier:
            return super()._get_socket(host, port, timeout)
        if timeout is not None and not timeout:
            raise ValueError('Non-blocking socket (timeout=0) is not supported')
        if self.debuglevel > 0:
            self._print_debug('connect: to', (host, port), self.source_address)        
        return self._proxifier.get_socket(self.source_address, host, port, timeout)

# ============================================================= #

class SMTP_SSL_Proxy(smtplib.SMTP_SSL):

    def __init__(self, host='', port=0, local_hostname=None, keyfile=None, certfile=None, timeout=object(), source_address=None, context=None, 
                 proxifier: Proxifier=None):        
        self._proxifier = proxifier
        super().__init__(host, port, local_hostname, keyfile, certfile, timeout, source_address, context)

    def _get_socket(self, host, port, timeout):
        if not self._proxifier:
            return super()._get_socket(host, port, timeout)
        if timeout is not None and not timeout:
            raise ValueError('Non-blocking socket (timeout=0) is not supported')
        if self.debuglevel > 0:
            self._print_debug('connect: to', (host, port), self.source_address)
        newsocket = self._proxifier.get_socket(self.source_address, host, port, timeout)
        return self.context.wrap_socket(newsocket, server_hostname=self._host)

# ============================================================= #

def send_email(body, subject, sender, receivers, smtp):
    is_ssl = smtp['protocol'].upper() == 'SSL'
    smtp_class = SMTP_SSL_Proxy if is_ssl else SMTP_Proxy
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['To'] = '; '.join(receivers)
        msg['From'] = sender
        msg.set_content(body)

        with smtp_class(smtp['server'], smtp['port'], proxifier=Proxifier.get_proxifier()) as emailer:
            emailer.login(smtp['login'], smtp['password'])
            if not is_ssl: 
                emailer.starttls()
            emailer.send_message(msg, sender, receivers)

        utils.log(f"--- Email sent to {msg['To']}")

    except smtplib.SMTPException as smtp_err:
        utils.log(f'SMTP ERROR: {str(smtp_err)}', how='exception')

    # except:
    #     traceback.print_exc()

    except Exception as err:
        utils.log(err, how='exception')