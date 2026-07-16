import threading
import requests
from collections import Counter

URL = "http://localhost:5000/home"
TOTAL_REQUESTS = 10000
CONCURRENT_THREADS = 5

results = Counter()
counter_lock = threading.Lock()

def send_request():
    requests_per_thread = TOTAL_REQUESTS // CONCURRENT_THREADS
    # Create a persistent session pool for this specific thread
    with requests.Session() as session:
        for _ in range(requests_per_thread):
            try:
                # Reuses the same underlying TCP connection connection across the loop
                resp = session.get(URL, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    msg = data.get("message", "")

                    if "Server:" in msg:
                        server_name = msg.split("Server:")[1].strip()
                        with counter_lock:
                            results[server_name] += 1
                else:
                    with counter_lock:
                        results[f"HTTP Error {resp.status_code}"] += 1
            except Exception as e:
                with counter_lock:
                    results[f"Errors ({type(e).__name__})"] += 1

if __name__ == "__main__":
    print(f"Launching {TOTAL_REQUESTS} requests using Keep-Alive connection pools across {CONCURRENT_THREADS} parallel threads...")

    threads = []
    for _ in range(CONCURRENT_THREADS):
        t = threading.Thread(target=send_request)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("\n================ EXPERIMENT RESULTS ================")
    total_successful = sum(count for server, count in results.items() if "server" in server)
    for server, count in sorted(results.items()):
        print(f"🔹 {server}: {count} requests handled ({(count/TOTAL_REQUESTS)*100:.2f}%)")
    print(f"====================================================")
    print(f"Total successful routed requests: {total_successful} / {TOTAL_REQUESTS}")
