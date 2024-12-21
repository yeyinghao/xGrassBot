# Copyright (C) 2024 officialputuid

import asyncio
import datetime
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
    format=(
        "<green>{time:DD/MM/YY HH:mm:ss}</green> | "
        "<level>{level:8} | {message}</level>"
    ),
    colorize=True
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

# Number of proxies to use /uid
ONETIME_PROXY = 100

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

# Ask user for node type (extension or desktop)
def get_node_type():
    node_type = ""
    while node_type not in ['extension', 'desktop']:
        node_type = input("🔵 Choose node type (extension/desktop): ").strip().lower()
        if node_type not in ['extension', 'desktop']:
            print("🔴 Invalid input. Please enter 'extension' or 'desktop'.")
    return node_type

node_type = get_node_type()
print(f"🔵 You selected: {node_type.capitalize()} node. ENJOY!\n")

def truncate_userid(user_id):
    return f"{user_id[:3]}--{user_id[-3:]}"

def truncate_proxy(proxy):
    return f"{proxy[:4]}--{proxy[-4:]}"

async def connect_to_wss(protocol_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, protocol_proxy))
    logger.info(f"UID: {truncate_userid(user_id)} | Device ID: {device_id} | Proxy: {truncate_proxy(protocol_proxy)}")

    while True:
        try:
            await asyncio.sleep(random.uniform(0.1, 1.0)) # reduced frequency
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; ARM Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            ]
            custom_headers = {
                "User-Agent": random.choice(user_agents)
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urilist = ["wss://proxy2.wynd.network:4444/", "wss://proxy2.wynd.network:4650/"]
            uri = random.choice(urilist)
            proxy = Proxy.from_url(protocol_proxy)

            if node_type == 'desktop':
                async with proxy_connect(
                    uri,
                    proxy=proxy,
                    ssl=ssl_context,
                    extra_headers={"User-Agent": custom_headers["User-Agent"]}
                ) as websocket:
                    logger.success(f"UID: {truncate_userid(user_id)} | Success connect to WS with Proxy: {truncate_proxy(protocol_proxy)}")

                    async def send_ping():
                        while True:
                            send_message = json.dumps({
                                "id": str(uuid.uuid4()),
                                "version": "1.0.0",
                                "action": "PING",
                                "data": {}
                            })
                            logger.debug(f"UID: {truncate_userid(user_id)} | Send PING message ID: {json.loads(send_message)['id']}")
                            await websocket.send(send_message)
                            rand_sleep = random.uniform(5, 30) # random delay + reduce bandwidth usage
                            logger.info(f"UID: {truncate_userid(user_id)} | Sleep for {rand_sleep:.2f} seconds")
                            await asyncio.sleep(rand_sleep)

                    send_ping_task = asyncio.create_task(send_ping())

                    try:
                        while True:
                            response = await websocket.recv()
                            message = json.loads(response)
                            simply_message = {
                                'id': message.get('id'),
                                'action': message.get('action')
                            }
                            logger.info(f"UID: {truncate_userid(user_id)} | Received message: {simply_message}")

                            custom_date = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

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
                                        "version": "4.30.0"
                                    }
                                }
                                logger.debug(f"UID: {truncate_userid(user_id)} | Send AUTH | ID: {auth_response['id']} | version: {auth_response['result']['version']}")
                                await websocket.send(json.dumps(auth_response))
                                logger.success(f"UID: {truncate_userid(user_id)} | Success AUTH with Device ID: {device_id}")
                            elif message.get("action") == "PONG":
                                pong_response = {"id": message["id"], "origin_action": "PONG"}
                                logger.debug(f"UID: {truncate_userid(user_id)} | Send PONG: {pong_response}")
                                await websocket.send(json.dumps(pong_response))
                                logger.success(f"UID: {truncate_userid(user_id)} | Success sent PONG | ID: {pong_response['id']} | Action: {pong_response['origin_action']}")
                            elif message.get("action") == "HTTP_REQUEST":
                                http_request_response = {"id": message["id"], "origin_action": "HTTP_REQUEST"}
                                logger.debug(f"UID: {truncate_userid(user_id)} | Send HTTP_REQUEST: {http_request_response}")
                                await websocket.send(json.dumps(http_request_response))
                                logger.success(f"UID: {truncate_userid(user_id)} | Success sent HTTP_REQUEST | ID: {http_request_response['id']} | Action: {http_request_response['origin_action']}")
                            elif message.get("action") == "OPEN_TUNNEL":
                                opentunnel_request_response = {
                                    "id": message["id"],
                                    "origin_action": "OPEN_TUNNEL",
                                    "result": {
                                        "url": message["url"],
                                        "status": 200,
                                        "status_text": "OK",
                                        "headers": {
                                            "content-type": "application/json; charset=utf-8",
                                            "date": custom_date,
                                            "keep-alive": "timeout=5",
                                            "proxy-connection": "keep-alive",
                                            "x-powered-by": "Express",
                                        }
                                    }
                                }
                                logger.debug(f"UID: {truncate_userid(user_id)} | Send OPEN_TUNNEL: {opentunnel_request_response}")
                                await websocket.send(json.dumps(opentunnel_request_response))
                                logger.success(f"UID: {truncate_userid(user_id)} | Success sent OPEN_TUNNEL | ID: {opentunnel_request_response['id']} | Action: {opentunnel_request_response['origin_action']}")
                    except websockets.exceptions.ConnectionClosed as e:
                        logger.error(f"UID: {truncate_userid(user_id)} | WebSocket closed unexpectedly | Proxy: {truncate_proxy(protocol_proxy)} | Error: {str(e)[:30]}**")
                    finally:
                        await websocket.close()
                        logger.warning(f"UID: {truncate_userid(user_id)} | WebSocket connection closed | Proxy: {truncate_proxy(protocol_proxy)}")
                        send_ping_task.cancel()
                        break

            elif node_type == 'extension':
                async with proxy_connect(
                    uri,
                    proxy=proxy,
                    ssl=ssl_context,
                    extra_headers={"Origin": "chrome-extension://ilehaonighjijnmpnagapkhpcdbhclfg", "User-Agent": custom_headers["User-Agent"]}
                ) as websocket:
                    logger.success(f"UID: {truncate_userid(user_id)} | Success connected to WS with Proxy: {truncate_proxy(protocol_proxy)}")

                    async def send_ping():
                        while True:
                            send_message = json.dumps({
                                "id": str(uuid.uuid4()),
                                "version": "1.0.0",
                                "action": "PING",
                                "data": {}
                            })
                            logger.debug(f"UID: {truncate_userid(user_id)} | Send PING | ID: {json.loads(send_message)['id']}")
                            await websocket.send(send_message)
                            rand_sleep = random.uniform(5, 30) # random delay + reduce bandwidth usage
                            logger.info(f"UID: {truncate_userid(user_id)} | Sleep for {rand_sleep:.2f} seconds")
                            await asyncio.sleep(rand_sleep)

                    send_ping_task = asyncio.create_task(send_ping())

                    try:
                        while True:
                            response = await websocket.recv()
                            message = json.loads(response)
                            simply_message = {
                                'id': message.get('id'),
                                'action': message.get('action')
                            }
                            logger.info(f"UID: {truncate_userid(user_id)} | Received message: {simply_message}")

                            custom_date = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

                            if message.get("action") == "AUTH":
                                auth_response = {
                                    "id": message["id"],
                                    "origin_action": "AUTH",
                                    "result": {
                                        "browser_id": device_id,
                                        "user_id": user_id,
                                        "user_agent": custom_headers['User-Agent'],
                                        "timestamp": int(time.time()),
                                        "device_type": "extension",
                                        "version": "4.26.2",
                                        "extension_id": "ilehaonighjijnmpnagapkhpcdbhclfg"
                                    }
                                }
                                logger.debug(f"UID: {truncate_userid(user_id)} | Send AUTH | ID: {auth_response['id']} | version: {auth_response['result']['version']}")
                                await websocket.send(json.dumps(auth_response))
                                logger.success(f"UID: {truncate_userid(user_id)} | Success AUTH with Device ID: {device_id}")
                            elif message.get("action") == "PONG":
                                pong_response = {"id": message["id"], "origin_action": "PONG"}
                                logger.debug(f"UID: {truncate_userid(user_id)} | Send PONG: {pong_response}")
                                await websocket.send(json.dumps(pong_response))
                                logger.success(f"UID: {truncate_userid(user_id)} | Success sent PONG | ID: {pong_response['id']} | Action: {pong_response['origin_action']}")
                            elif message.get("action") == "HTTP_REQUEST":
                                http_request_response = {"id": message["id"], "origin_action": "HTTP_REQUEST"}
                                logger.debug(f"UID: {truncate_userid(user_id)} | Send HTTP_REQUEST: {http_request_response}")
                                await websocket.send(json.dumps(http_request_response))
                                logger.success(f"UID: {truncate_userid(user_id)} | Success sent HTTP_REQUEST | ID: {http_request_response['id']} | Action: {http_request_response['origin_action']}")
                            elif message.get("action") == "OPEN_TUNNEL":
                                opentunnel_request_response = {
                                    "id": message["id"],
                                    "origin_action": "OPEN_TUNNEL",
                                    "result": {
                                        "url": message["url"],
                                        "status": 200,
                                        "status_text": "OK",
                                        "headers": {
                                            "content-type": "application/json; charset=utf-8",
                                            "date": custom_date,
                                            "keep-alive": "timeout=5",
                                            "proxy-connection": "keep-alive",
                                            "x-powered-by": "Express",
                                        }
                                    }
                                }
                                logger.debug(f"UID: {truncate_userid(user_id)} | Send OPEN_TUNNEL: {opentunnel_request_response}")
                                await websocket.send(json.dumps(opentunnel_request_response))
                                logger.success(f"UID: {truncate_userid(user_id)} | Success sent OPEN_TUNNEL | ID: {opentunnel_request_response['id']} | Action: {opentunnel_request_response['origin_action']}")
                    except websockets.exceptions.ConnectionClosed as e:
                        logger.error(f"UID: {truncate_userid(user_id)} | WebSocket closed unexpectedly | Proxy: {truncate_proxy(protocol_proxy)} | Error: {str(e)[:30]}**")
                    finally:
                        await websocket.close()
                        logger.warning(f"UID: {truncate_userid(user_id)} | WebSocket connection closed | Proxy: {truncate_proxy(protocol_proxy)}")
                        send_ping_task.cancel()
                        break

        except Exception as e:
            logger.error(f"UID: {truncate_userid(user_id)} | Error with proxy {truncate_proxy(protocol_proxy)} ➜ {str(e)[:30]}**")
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
                    logger.warning(f"UID: {truncate_userid(user_id)} | Removing error proxy from list ➜ {truncate_proxy(protocol_proxy)}")
                    remove_proxy_from_list(protocol_proxy)
                    return None
            else:
                if "Device creation limit exceeded" in str(e):
                    logger.warning(f"UID: {truncate_userid(user_id)} | Removing error proxy from list ➜ {truncate_proxy(protocol_proxy)}")
                    remove_proxy_from_list(protocol_proxy)
                    return None
            continue

async def main():
    with open('uid.txt', 'r') as file:
        user_ids = file.read().splitlines()

    with open('proxy.txt', 'r') as file:
        all_proxies = file.read().splitlines()

    used_proxies = min(ONETIME_PROXY, len(all_proxies))
    active_proxies = random.sample(all_proxies, used_proxies)

    tasks = {}

    for user_id in user_ids:
        for proxy in active_proxies:
            await asyncio.sleep(random.uniform(2.0, 4.0))
            task = asyncio.create_task(connect_to_wss(proxy, user_id))
            tasks[task] = (proxy, user_id)

    while True:
        done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task.result() is None:
                failed_proxy, user_id = tasks[task]
                logger.warning(f"UID: {truncate_userid(user_id)} | Removing and replacing failed proxy: {truncate_proxy(failed_proxy)}")

                if failed_proxy in active_proxies:
                    active_proxies.remove(failed_proxy)

                new_proxy = random.choice(all_proxies)
                active_proxies.append(new_proxy)

                await asyncio.sleep(random.uniform(2.0, 4.0))
                new_task = asyncio.create_task(connect_to_wss(new_proxy, user_id))
                tasks[new_task] = (new_proxy, user_id)
                logger.success(f"UID: {truncate_userid(user_id)} | Successfully replaced failed proxy: {truncate_proxy(failed_proxy)} with: {truncate_proxy(new_proxy)}")

            tasks.pop(task)

        for proxy in set(active_proxies) - {task[0] for task in tasks.values()}:
            for user_id in user_ids:
                await asyncio.sleep(random.uniform(2.0, 4.0))
                new_task = asyncio.create_task(connect_to_wss(proxy, user_id))
                tasks[new_task] = (proxy, user_id)
                logger.success(f"UID: {truncate_userid(user_id)} | Successfully started task with proxy: {truncate_proxy(proxy)}")

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
