import os

with open("logs2.txt", "r", encoding="utf-16", errors="ignore") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "Exception" in line or "Error" in line or "Traceback" in line:
            print("FOUND ERROR at line", i)
            # print surrounding lines
            start = max(0, i-5)
            end = min(len(lines), i+15)
            for j in range(start, end):
                print(lines[j].strip())
            print("-" * 50)
