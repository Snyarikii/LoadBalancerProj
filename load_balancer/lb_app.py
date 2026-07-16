import os
import random
import time
import threading
import requests
from flask import Flask, request, jsonify
from hash_ring import ConsistentHashRing

app = Flask(__name__)

DEFAULT_N = 3
managed_replicas = []
ring_lock = threading.Lock()

ring = ConsistentHashRing(slots=512, v_replicas=50)

def spawn_container(hostname):
    cmd = f"sudo docker run --name {hostname} --network net1 --network-alias {hostname} -e SERVER_ID={hostname} -d server_image:latest"
    os.system(cmd)
    time.sleep(3)  # Grace period for Flask to boot up

def kill_container(hostname):
    """Stops and purges a web server container instantly."""
    os.system(f"sudo docker stop {hostname} && sudo docker rm {hostname}")

def initialize_cluster():
    """Initializes the baseline cluster configuration with N=3 server containers."""
    global managed_replicas
    with ring_lock:
        for i in range(1, DEFAULT_N + 1):
            name = f"server-{i}"  # Uses hyphen instead of underscore
            managed_replicas.append(name)
            spawn_container(name)
            ring.add_server(name)

# 1. Endpoint (/rep, method=GET)
@app.route('/rep', methods=['GET'])
def get_replicas():
    with ring_lock:
        response = {
            "message": {
                "N": len(managed_replicas),
                "replicas": managed_replicas
            },
            "status": "successful"
        }
    return jsonify(response), 200

# 2. Endpoint (/add, method=POST)
@app.route('/add', methods=['POST'])
def add_replicas():
    global managed_replicas
    payload = request.get_json()
    n = payload.get('n')
    hostnames = payload.get('hostnames', [])
    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure"
        }), 400
    with ring_lock:
        for i in range(n):
            if i < len(hostnames):
                name = hostnames[i]
            else:
                name = f"server-auto-{random.randint(1000, 9999)}"  # Uses hyphen
            if name not in managed_replicas:
                managed_replicas.append(name)
                spawn_container(name)
                ring.add_server(name)
        response = {
            "message": {
                "N": len(managed_replicas),
                "replicas": managed_replicas
            },
            "status": "successful"
        }
    return jsonify(response), 200

# 3. Endpoint (/rm, method=DELETE)
@app.route('/rm', methods=['DELETE'])
def remove_replicas():
    global managed_replicas
    payload = request.get_json()
    n = payload.get('n')
    hostnames = payload.get('hostnames', [])
    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure"
        }), 400
    with ring_lock:
        to_remove = []
        for name in hostnames:
            if name in managed_replicas:
                to_remove.append(name)
        remaining = [r for r in managed_replicas if r not in to_remove]
        while len(to_remove) < n and remaining:
            chosen = random.choice(remaining)
            to_remove.append(chosen)
            remaining.remove(chosen)
        for name in to_remove:
            if name in managed_replicas:
                managed_replicas.remove(name)
                ring.remove_server(name)
                kill_container(name)
        response = {
            "message": {
                "N": len(managed_replicas),
                "replicas": managed_replicas
            },
            "status": "successful"
        }
    return jsonify(response), 200

# 4. Endpoint (/<path>, method=GET)
@app.route('/<path:path>', methods=['GET'])
def route_request(path):
    if path not in ['home', 'heartbeat']:
        return jsonify({
            "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
            "status": "failure"
        }), 400

    request_id = str(random.randint(100000, 999999))

    with ring_lock:
        target_server = ring.get_server(request_id)

    if not target_server:
        return jsonify({"message": "No active backend servers available", "status": "failure"}), 500

    try:
        url = f"http://{target_server}:5000/{path}"
        server_response = requests.get(url, timeout=5)
        return server_response.text, server_response.status_code
    except requests.exceptions.RequestException:
        return jsonify({"message": f"Failed to connect to backend {target_server}", "status": "failure"}), 502

def heartbeat_monitor():
    """Background loop that continuously monitors server health and manages auto-recovery."""
    global managed_replicas
    while True:
        time.sleep(10)
        with ring_lock:
            active_snapshot = list(managed_replicas)

        for server in active_snapshot:
            try:
                url = f"http://{server}:5000/heartbeat"
                resp = requests.get(url, timeout=5)
                if resp.status_code != 200:
                    raise Exception(f"Unhealthy status code: {resp.status_code}")
            except Exception as e:
                print(f"[ALERT] {server} failed healthcheck. Reason: {e}. Remediation initiated...", flush=True)
                with ring_lock:
                    if server in managed_replicas:
                        managed_replicas.remove(server)
                        ring.remove_server(server)
                        kill_container(server)

                        new_name = f"server-rec-{random.randint(1000, 9999)}"  # Uses hyphen
                        managed_replicas.append(new_name)
                        spawn_container(new_name)
                        ring.add_server(new_name)
                        print(f"[RECOVERED] Replaced {server} with brand-new instance: {new_name}", flush=True)

if __name__ == '__main__':
    initialize_cluster()
    monitor_thread = threading.Thread(target=heartbeat_monitor, daemon=True)
    monitor_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
