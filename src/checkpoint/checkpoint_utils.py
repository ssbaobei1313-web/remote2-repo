import os


class Checkpoint:
    def __init__(self, path: str):
        self.path = path

        os.makedirs(os.path.dirname(path), exist_ok=True)

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.processed = set(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            self.processed = set()

    def is_processed(self, account: str):
        return account in self.processed

    def mark_processed(self, account: str):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(account + "\n")
        self.processed.add(account)
