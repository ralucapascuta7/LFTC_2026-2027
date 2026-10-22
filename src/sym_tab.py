"""Symbol table for AquaLight, implemented as a hash table with separate chaining.

A position in the table is the pair (bucket, index): the bucket in the hash
table and the index of the entry inside the chain (a linked list).
"""


class Node:
    """One entry of a chain (singly linked list)."""

    def __init__(self, key):
        self.key = key
        self.next = None


class SymbolTable:
    def __init__(self, num_buckets=31):
        if num_buckets <= 0:
            raise ValueError("num_buckets must be positive")
        self.num_buckets = num_buckets
        self._buckets = [None] * num_buckets 
        self._size = 0

    @staticmethod
    def _hash(key):
        """djb2 hash function (kept on 64 bits)."""
        h = 5381
        for ch in key:
            h = (h * 33 + ord(ch)) & 0xFFFFFFFFFFFFFFFF
        return h

    def _bucket_of(self, key):
        return self._hash(key) % self.num_buckets

    def insert(self, key):
        """Adds key if it is missing; returns its position (bucket, index).

        New entries are added at the end of the chain, so positions never change.
        """
        bucket = self._bucket_of(key)
        index, last, node = 0, None, self._buckets[bucket]
        while node is not None:
            if node.key == key:
                return bucket, index
            last, node = node, node.next
            index += 1
        new_node = Node(key)
        if last is None:
            self._buckets[bucket] = new_node
        else:
            last.next = new_node
        self._size += 1
        return bucket, index

    def lookup(self, key):
        """Returns the position of key, or None if it is not in the table."""
        bucket = self._bucket_of(key)
        index, node = 0, self._buckets[bucket]
        while node is not None:
            if node.key == key:
                return bucket, index
            node = node.next
            index += 1
        return None

    def __len__(self):
        return self._size

    def items(self):
        """Yields (bucket, index, key) for every entry, bucket by bucket."""
        for bucket, node in enumerate(self._buckets):
            index = 0
            while node is not None:
                yield bucket, index, node.key
                node = node.next
                index += 1

    def close(self):
        self._buckets = [None] * self.num_buckets
        self._size = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()