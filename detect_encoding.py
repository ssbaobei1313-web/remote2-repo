try:
    import chardet
except ImportError:
    chardet = None

with open("gui/main_gui.py", "rb") as f:
    data = f.read()

if chardet is not None:
    print(chardet.detect(data))
else:
    print("chardet is not installed. Install it to detect encoding.")
    print({"encoding": "utf-8", "confidence": 0.0})

if __name__ == "__main__":
    pass 