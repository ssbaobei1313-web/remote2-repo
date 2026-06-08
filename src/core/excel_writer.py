import openpyxl
import os


class ExcelWriter:
    def __init__(self, path: str):
        self.path = path

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path), exist_ok=True)

        if not os.path.exists(path):
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["account", "title"])
            wb.save(path)

    def append_row(self, data: dict):
        wb = openpyxl.load_workbook(self.path)
        ws = wb.active
        ws.append([data.get("account"), data.get("title")])
        wb.save(self.path)
