def outputs_equal(stdout: str, expected: str) -> bool:
    stdout = stdout.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in stdout.split("\n")]
    # 忽略末尾多出的""（由于多余的换行产生）
    while lines and lines[-1] == "":
        lines.pop() # 删除末尾元素
    stdout = "\n".join(lines)

    expected = expected.replace("\r\n", "\n").replace("\r", "\n")
    e_lines = [e_line.rstrip(" \t") for e_line in expected.split("\n")]
    # 忽略末尾多出的""（由于多余的换行产生）
    while e_lines and e_lines[-1] == "":
        e_lines.pop() # 删除末尾元素
    expected = "\n".join(e_lines)
    return stdout == expected