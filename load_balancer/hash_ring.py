import hashlib

class ConsistentHashRing:
    def __init__(self, slots=512, v_replicas=50):
        self.slots_count = slots
        self.v_replicas = v_replicas
        self.ring = [None] * self.slots_count

    def _hash(self, key):

        encoded_key = str(key).encode('utf-8')
        # Convert MD5 hex digest to a large base-16 integer, then wrap it within the 512 slot boundary
        return int(hashlib.md5(encoded_key).hexdigest(), 16) % self.slots_count

    def request_hash(self, request_id):

        return self._hash(request_id)

    def server_hash(self, server_name, v_id):

        return self._hash(f"{server_name}-v{v_id}")

    def add_server(self, server_name):

        for j in range(self.v_replicas):
            slot = self.server_hash(server_name, j)
            # Linear probing to handle slot collisions gracefully
            while self.ring[slot] is not None:
                slot = (slot + 1) % self.slots_count
            self.ring[slot] = server_name

    def remove_server(self, server_name):

        for slot in range(self.slots_count):
            if self.ring[slot] == server_name:
                self.ring[slot] = None

    def get_server(self, request_id):

        if all(slot is None for slot in self.ring):
            return None

        start_slot = self.request_hash(request_id)
        slot = start_slot

        # Scan clockwise until a server replica is found
        while self.ring[slot] is None:
            slot = (slot + 1) % self.slots_count
        return self.ring[slot]
