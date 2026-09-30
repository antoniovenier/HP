import os, sys
def test_x():
    print("HP_LOCAL", os.environ.get("HP_LOCAL"))
    print([p for p in sys.path if "HP" in p])
