# -*- coding: utf-8 -*-
"""从 youxi.py 重新抽取剧情到 game_data.py（改完剧情后跑一次）"""
import ast
import io
import os

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "youxi.py")
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_data.py")


def main():
    src = io.open(SRC, encoding="utf-8").read()
    start = src.index("SCENES = {")
    i = src.index("{", start)
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    literal = src[i:end]
    scenes = ast.literal_eval(literal)
    header = ('# -*- coding: utf-8 -*-\n'
              '"""剧情数据（由 youxi.py 自动抽取，改剧情请改 youxi.py 后重新同步）"""\n\n')
    io.open(DST, "w", encoding="utf-8").write(header + "SCENES = " + literal + "\n")
    print(f"已同步 {len(scenes)} 个场景 -> {DST}")


if __name__ == "__main__":
    main()
