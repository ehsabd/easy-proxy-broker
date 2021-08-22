
#TODO: add a mechanism to detect allfailing proxies
#TODO: when we have enough proxies in our pool don't get new ones
# Easy Proxy Broker (v0.2) by https://reddit.com/user/fantasticoder 
import asyncio
from proxybroker import Broker
from pathlib import Path
from datetime import datetime
import time
from random import randint
import json

class EasyProxyBroker:
        
    def __init__(self, proxy_pool_file = 'proxies.json', proxy_types=['HTTPS'] , num_proxy_appended = 3, get_proxy_max_attempts = 10):
        self.proxies = asyncio.Queue()
        self.broker = Broker(self.proxies)
        self.my_proxy_pool = []
        self.num_proxy_appended = num_proxy_appended
        self.get_proxy_max_attempts = get_proxy_max_attempts
        self.proxy_types = proxy_types
        self.proxy_pool_file = proxy_pool_file
        self.load_proxy_pool()

    def load_proxy_pool(self):
        try:
            file = Path(self.proxy_pool_file)
            if file.exists():
                self.my_proxy_pool = json.loads(file.read_text())
        except:
            self.log('Error loading file %s' % self.proxy_pool_file)
    def save_proxy_pool(self):
        with open(self.proxy_pool_file,'w') as f:
            json.dump(self.my_proxy_pool,f)

    def get_proxy(self):
        return self.my_proxy_pool[0]

    def rotate_proxy(self):
        self.my_proxy_pool = self.my_proxy_pool[1:] + self.my_proxy_pool[0:1]
        self.save_proxy_pool()

    def log(self, content):
        print (str(datetime.now())+' : '+str(content))

    def handle_exception(self, loop, context):
        # context["message"] will always be there; but context["exception"] may not
        msg = context.get("exception", context["message"])
        self.log(f"Caught exception: {msg}")
        time.sleep(randint(3,10))
        
    async def add_proxies(self):
    
        i = 0
    
        while True:
            i = i + 1
            self.log('Awaiting proxies.get() ...')
            proxy = await asyncio.wait_for(self.proxies.get(), timeout=30)
            time.sleep(randint(3,10))
            if proxy is None or i>= self.get_proxy_max_attempts: break
            p = proxy.host+':'+str(proxy.port)
            self.my_proxy_pool.append(p)
            self.log('%s appended to proxy pool' % p)

    def append_new_proxies(self):
        try:
            loop = asyncio.get_event_loop()
            tasks = asyncio.gather(
            self.broker.find(types=self.proxy_types, limit=self.num_proxy_appended),
            self.add_proxies())
            loop.set_exception_handler(self.handle_exception)
            loop.run_until_complete(tasks)
            self.my_proxy_pool = list(set(self.my_proxy_pool)) #remove dups
            self.save_proxy_pool()
        except:
            self.log('Error appending new proxies')