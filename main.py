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

logger.remove()
logger.add(
    sink=lambda msg: print(msg, end=''),
    format="{time:DD/MM/YY HH:mm:ss} | <level>{level:8}</level> | <level>{message}</level>"
)

# main.py
def print_header():
    cn = pyfiglet.figlet_format("xGrassNode")
    print(cn)
    print("🌱 Season 2")
    print("🎨 by \033]8;;https://github.com/officialputuid\033\\officialputuid\033]8;;\033\\")
    print('🎁 \033]8;;https://paypal.me/IPJAP\033\\Paypal.me/IPJAP\033]8;;\033\\ — \033]8;;https://trakteer.id/officialputuid\033\\Trakteer.id/officialputuid\033]8;;\033\\')

# Initialize the header
print_header()

ONETIME_PROXY = 25

# Read UID and Proxy count
def read_uid_and_proxy():
    with open('uid.txt', 'r') as file:
        uid_count = sum(1 for line in file)

    with open('proxy.txt', 'r') as file:
        proxy_count = sum(1 for line in file)

    return uid_count, proxy_count

uid_count, proxy_count = read_uid_and_proxy()

print()
print(f"🔑 UID: {uid_count}.")
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

def truncate_userid(user_id):
    return f"{user_id[:4]}--{user_id[-4:]}"

def truncate_proxy(proxy):
    return f"{proxy[:6]}--{proxy[-10:]}"

async def connect_to_wss(protocol_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, protocol_proxy))
    logger.info(f"User ID: {truncate_userid(user_id)}, Device ID: {device_id}, Using Proxy: {truncate_proxy(protocol_proxy)}")

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
            proxy = Proxy.from_url(protocol_proxy)

            async with proxy_connect(
                uri,
                proxy=proxy,
                ssl=ssl_context,
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
                        logger.debug(f"User ID: {truncate_userid(user_id)} | Sending PING message ID: {json.loads(send_message)['id']}")
                        await websocket.send(send_message)
                        rand_sleep = random.uniform(50, 100) # random delay + increased interval to reduce bandwidth usag
                        logger.debug(f"User ID: {truncate_userid(user_id)} | Sleeping for {rand_sleep:.2f} seconds")
                        await asyncio.sleep(rand_sleep)

                init_sleep = random.uniform(4, 24) # random delay
                logger.debug(f"User ID: {truncate_userid(user_id)} | Initial sleep for {init_sleep:.2f} seconds")
                await asyncio.sleep(init_sleep)
                send_ping_task = asyncio.create_task(send_ping())

                try:
                    while True:
                        response = await websocket.recv()
                        message = json.loads(response)
                        logger.info(f"User ID: {truncate_userid(user_id)} | Received message: {message}")

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
                            logger.debug(f"User ID: {truncate_userid(user_id)} | Sending AUTH response ID: {auth_response['id']}")
                            await websocket.send(json.dumps(auth_response))

                        elif message.get("action") == "PONG":
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            logger.debug(f"User ID: {truncate_userid(user_id)} | Sending PONG response: {pong_response}")
                            await websocket.send(json.dumps(pong_response))

                finally:
                    send_ping_task.cancel()

        except Exception as e:
            logger.error(f"User ID: {truncate_userid(user_id)} | Error with proxy {truncate_proxy(protocol_proxy)} ➜ {str(e)[:30]}**")
            error_conditions = [
                "Host unreachable",
                "[SSL: WRONG_VERSION_NUMBER]", 
                "invalid length of packed IP address string", 
                "Empty connect reply",
                "Device creation limit exceeded",
                "[Errno 111] Could not connect to proxy",
                "sent 1011 (internal error) keepalive ping timeout; no close frame received"
            ]

            if remove_on_all_errors:
                if any(error_msg in str(e) for error_msg in error_conditions):
                    logger.info(f"User ID: {truncate_userid(user_id)} | Removing error proxy from the list ➜ {truncate_proxy(protocol_proxy)}")
                    remove_proxy_from_list(protocol_proxy)
                    return None
            else:
                if "Device creation limit exceeded" in str(e):
                    logger.info(f"User ID: {truncate_userid(user_id)} | Removing error proxy from the list ➜ {truncate_proxy(protocol_proxy)}")
                    remove_proxy_from_list(protocol_proxy)
                    return None
            continue

async def main():
    with open('uid.txt', 'r') as file:
        user_ids = file.read().splitlines()

    with open('proxy.txt', 'r') as file:
        all_proxies = file.read().splitlines()

    active_proxies = random.sample(all_proxies, ONETIME_PROXY)

    tasks = {}
    for user_id in user_ids:
        for proxy in active_proxies:
            task = asyncio.create_task(connect_to_wss(proxy, user_id))
            tasks[task] = proxy

    while True:
        done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            if task.result() is None:
                failed_proxy = tasks[task]
                logger.info(f"Removing and replacing failed proxy: {truncate_proxy(failed_proxy)}")

                if failed_proxy in active_proxies:
                    active_proxies.remove(failed_proxy)

                new_proxy = random.choice(all_proxies)
                active_proxies.append(new_proxy)
                new_task = asyncio.create_task(connect_to_wss(new_proxy, user_id))
                tasks[new_task] = new_proxy

            tasks.pop(task)

        for proxy in set(active_proxies) - set(tasks.values()):
            new_task = asyncio.create_task(connect_to_wss(proxy, user_id))
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
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info(f"Program terminated by user. ENJOY!\n")
