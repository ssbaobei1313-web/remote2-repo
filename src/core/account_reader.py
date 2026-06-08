class AccountReader:
    @staticmethod
    def read_accounts(path: str):
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
