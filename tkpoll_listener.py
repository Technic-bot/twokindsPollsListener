#!/usr/bin/env python

import asyncio
import websockets

import json
import logging
import argparse

from datetime import datetime

def proc_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session')
    parser.add_argument('--logfile')
    return parser.parse_arguments()


class tkPollsLister():
    def __init__(self, spectate=False, sess_token=None, logfile=''):
        self.uri = "wss://tkpolls.com/voter"
        if spectate:
            uri = "wss://tkpolls.com/spectatorws"
        self.token = sess_token
        self.logfile = logfile
        self.make_head();
        self.setup_logging();
        return

    def setup_logging(self):
        """Configures a logger for the application."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter

        if not logger.handlers:  # Prevent duplicate handlers
            # File handler (DEBUG and above)
            if self.logfile:
                file_handler = logging.FileHandler(self.logfile)
            else: 
                file_handler = logging.FileHandler('tkpolls_listener.log')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)

            # Console handler (WARNING and above)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter("%(levelname)s: %(message)s")
            console_handler.setFormatter(console_formatter)

            # Add handlers
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        self.logger = logger
        return

    def make_head(self):
        self.agent = ("Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0)"
                      " Gecko/20100101 Firefox/121.0")
        self.extra_head = { 
            #"Cookie": "sesh=bYOc9B5AOiscAXpctJjTJu6CyMBtonSa",
            #"Accept-Language": "en-US,en;q=0.5",
            #"Accept-Encoding": "gzip, deflate, br",
            #"Sec-WebSocket-Version": 13,
            "Origin": "https://tkpolls.com",
            #"Sec-WebSocket-Extensions": "permessage-deflate",
            #"Sec-WebSocket-Key": "7nyYKpXbmqXwlu27lPc3rg==",
            "Connection": "keep-alive, Upgrade",
            "Cookie": f"sesh=yYpJmbuHOtWS4HFKQqmB9YHB4O8XW3m_",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "websocket",
            "Sec-Fetch-Site": "same-origin",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Upgrade": "websocket"}
        return

    async def connect(self):
        self.logger.info(f"Connecting to {self.uri}")
        async with websockets.connect(
                self.uri, 
                user_agent_header=self.agent,
                extra_headers=self.extra_head) as websocket:
            
            self.logger.info(f"Authenticating as {self.token}")
            await websocket.send(f'auth: {self.token}')
            async for message in websocket:
                await websocket.send('ack')
                try: 
                    response = json.loads(message)
                    # time=datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
                    # filename = f'./messages/{mtype}-{time}.json'
                    mtype = response['Mtype']
                    self.logger.info(f"Got message type: {mtype}")
                    self.logger.info(f"{response}")
                    # with open(filename,'w') as output_file:
                    #     json.dump(response, output_file)
                except ValueError as e:
                    self.logger.info(f"Heartbeat: {message}")
                except KeyError as e:
                    self.logger.error(e)


if __name__ == "__main__":
    listener = tkPollsLister(sess_token='yYpJmbuHOtWS4HFKQqmB9YHB4O8XW3m_') 
    asyncio.run(listener.connect())
