# Copyright (C) 2024 officialputuid

import asyncio
import json
import random
import ssl
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
import pyfiglet

# main.py
def print_header():
    cn = pyfiglet.figlet_format("xGrassDesktopNode")
    print(cn)
    print("🌱 Season 2")
    print("🎨 by \033]8;;https://github.com/officialputuid\033\\officialputuid\033]8;;\033\\")
    print('🎁 \033]8;;https://paypal.me/IPJAP\033\\Paypal.me/IPJAP\033]8;;\033\\ — \033]8;;https://trakteer.id/officialputuid\033\\Trakteer.id/officialputuid\033]8;;\033\\')

# Initialize the header
print_header()

HIDE_PROXY = "(🌐🔒🧩)"
ONETIME_PROXY = 50

# Read UID and Proxy count
def read_uid_and_proxy():
    with open('uid.txt', 'r') as file:
        uid_content = file.read().strip()

    with open('proxy.txt', 'r') as file:
        proxy_count = sum(1 for line in file)

    return uid_content, proxy_count

uid_content, proxy_count = read_uid_and_proxy()

print()
print(f"🔑 UID: {uid_content}.")
print(f"🌐 Loaded {proxy_count} proxies.")
print(f"🌐 Active proxy loaded per-task: {ONETIME_PROXY} proxies.")
print()

# Get User input for proxy failure handling
def get_user_input():
    user_input = ""
    while user_input not in ['yes', 'no']:
        user_input = input("🔵 Do you want to remove the proxy if there is a specific failure (yes/no)? ").strip().lower()
        if user_input not in ['yes', 'no']:
            print("🔴 Invalid input. Please enter 'yes' or 'no'.")
    return user_input == 'yes'

remove_on_all_errors = get_user_input()
print(f"🔵 You selected: {'Yes' if remove_on_all_errors else 'No'}, ENJOY!\n")

async def connect_to_wss(protocol_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, protocol_proxy))
    logger.info(f"🖥️ Device ID: {device_id}")

    while True:
        try:
            await asyncio.sleep(random.uniform(0.1, 1.0))  # reduced frequency
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urilist = ["wss://proxy2.wynd.network:4444/", "wss://proxy2.wynd.network:4650/"]
            uri = random.choice(urilist)
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(protocol_proxy)

            async with proxy_connect(
                uri,
                proxy=proxy,
                ssl=ssl_context,
                server_hostname=server_hostname,
                extra_headers={"User-Agent": custom_headers["User-Agent"]}
            ) as websocket:

                async def send_ping():
                    while True:
                        send_message = json.dumps({
                            "id": str(uuid.uuid4()),
                            "version": "1.0.0",
                            "action": "PING",
                            "data": {}
                        })
                        logger.debug(f"🚀 Sending PING message: {send_message}")
                        await websocket.send(send_message)
                        # Random delay between 5-10s
                        rand_sleep = random.uniform(5, 10)
                        logger.debug(f"⏳ Sleeping for {rand_sleep:.2f} seconds")
                        await asyncio.sleep(rand_sleep)

                # random delay between 1-4s
                init_sleep = random.uniform(1, 4)
                logger.debug(f"⏳ Initial sleep for {init_sleep:.2f} seconds")
                await asyncio.sleep(init_sleep)
                send_ping_task = asyncio.create_task(send_ping())

                try:
                    while True:
                        response = await websocket.recv()
                        message = json.loads(response)
                        logger.info(f"🌟 Received message: {message}")

                        if message.get("action") == "AUTH":
                            auth_response = {
                                "id": message["id"],
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": device_id,
                                    "user_id": user_id,
                                    "user_agent": custom_headers['User-Agent'],
                                    "timestamp": int(time.time()),
                                    "device_type": "desktop",
                                    "version": "4.29.0"
                                }
                            }
                            logger.debug(f"🚀 Sending AUTH response: {auth_response}")
                            await websocket.send(json.dumps(auth_response))

                        elif message.get("action") == "PONG":
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            logger.debug(f"🚀 Sending PONG response: {pong_response}")
                            await websocket.send(json.dumps(pong_response))

                finally:
                    send_ping_task.cancel()

        except Exception as e:
            logger.error(f"🔴 Error with proxy {HIDE_PROXY} ➜  {str(e)}")
            error_conditions = [
                "Host unreachable",
                "[SSL: WRONG_VERSION_NUMBER]", 
                "invalid length of packed IP address string", 
                "Empty connect reply",
                "Device creation limit exceeded", 
                "sent 1011 (internal error) keepalive ping timeout; no close frame received"
            ]

            if remove_on_all_errors:
                if any(error_msg in str(e) for error_msg in error_conditions):
                    logger.info(f"🔵 (TRUE) Removing error proxy from the list ➜  {HIDE_PROXY}")
                    remove_proxy_from_list(protocol_proxy)
                    return None
            else:
                if "Device creation limit exceeded" in str(e):
                    logger.info(f"🔵 (FALSE) Removing error proxy from the list ➜  {HIDE_PROXY}")
                    remove_proxy_from_list(protocol_proxy)
                    return None
            continue

async def main():
    with open('uid.txt', 'r') as file:
        _user_id = file.read().strip()

    with open('proxy.txt', 'r') as file:
        all_proxies = file.read().splitlines()

    active_proxies = random.sample(all_proxies, ONETIME_PROXY)
    tasks = {asyncio.create_task(connect_to_wss(proxy, _user_id)): proxy for proxy in active_proxies}

    while True:
        done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            if task.result() is None:
                failed_proxy = tasks[task]
                logger.info(f"🔵 Removing and replacing failed proxy: {failed_proxy}")
                active_proxies.remove(failed_proxy)
                new_proxy = random.choice(all_proxies)
                active_proxies.append(new_proxy)
                new_task = asyncio.create_task(connect_to_wss(new_proxy, _user_id))
                tasks[new_task] = new_proxy

            tasks.pop(task)

        for proxy in set(active_proxies) - set(tasks.values()):
            new_task = asyncio.create_task(connect_to_wss(proxy, _user_id))
            tasks[new_task] = proxy

def remove_proxy_from_list(proxy):
    with open("proxy.txt", "r+") as file:
        lines = file.readlines()
        file.seek(0)
        for line in lines:
            if line.strip() != proxy:
                file.write(line)
        file.truncate()

if __name__ == '__main__':
    asyncio.run(main())
