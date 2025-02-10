#!/usr/bin/env python

import asyncio
import websockets

import json
import logging
import argparse

from datetime import datetime

def proc_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token')
    parser.add_argument('--logfile')
    parser.add_argument('--poll-dir')
    parser.add_argument('--suggestions')
    return parser.parse_args()


class tkPollsLister():
    def __init__(self, 
            spectate=False, sess_token=None, logfile='',
            poll_dir='', sugg_file=None):
        self.uri = "wss://tkpolls.com/voter"
        if not sess_token:
            uri = "wss://tkpolls.com/spectatorws"
        self.token = sess_token
        self.logfile = logfile
        self.poll_dir = poll_dir
        self.make_head();
        self.setup_logging();
        self.options = {}
        self.suggs = []
        self.parse_suggestions(sugg_file)
        return

    def parse_suggestions(self, file):
        """ Read all suggestion in file turn to lower case and remove
            stray white space"""
        if not file:
            return 

        with open(file, 'r') as sug_file:
            self.logger.info(f"Reading suggestion file: {file}")
            for line in sug_file:
                sugg = line.lower()
                sugg = sugg.strip()
                self.suggs.append(sugg)
                self.logger.info(f"Got user suggestion: {sugg}")
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

    async def vote(self):
        """ From page source return a string of characters corresponding to votes"""
        if not self.suggs:
            return

        logger.info(f"Final vote string: {self.vote_str}")
        await websocket.send(f'ballot: {self.vote_str}')
        return 

    def store_polls(self, response):
        if self.poll_dir:
            poll_end = datetime.fromtimestamp(response['Ends'])
            poll_end_str = poll_end.strftime("%Y_%m_%d__%H_%M_%S")
            title = response['Title'].replace(' ', '_')
            filename = self.poll_dir + title + "_" + poll_end_str + ".json"
            self.logger.info(f"Saving to {filename}")
            with open(filename,'w') as output_file:
                 json.dump(response, output_file)
        return

    def get_votes(self):
        vote_str = ''
        for sug in self.suggs:
            for letter, opt in self.options.items():
                proc_opt = opt.lower().strip()
                if sug in proc_opt:
                    self.logger.info(
                        f"Found matching suggestion @ {letter}: {sug} -> {opt}")
                    letter_int = int(letter) 
                    letter_char = chr(letter_int) 
                    vote_str += letter_char
        self.vote_str = vote_str
        self.logger.info(f"Total suggestions string: {self.vote_str}")
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
                    if mtype == 'poll':
                        self.options = response['Options']
                        self.store_polls(response)
                        self.get_votes()
                    if mtype == 'call':
                        self.logger.info("Sending votes")
                        await self.vote()
                except ValueError as e:
                    self.logger.info(f"Heartbeat: {message}")
                except KeyError as e:
                    self.logger.error(e)


if __name__ == "__main__":
    args = proc_opts()
    listener = tkPollsLister(
            sess_token=args.token,
            poll_dir='./polls/',
            sugg_file=args.suggestions) 
    asyncio.run(listener.connect())
