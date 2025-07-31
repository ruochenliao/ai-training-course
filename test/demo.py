import anyio
from claude_code_sdk import query, ClaudeCodeOptions
from pathlib import Path


async def main():
    options = ClaudeCodeOptions(
        max_turns=3,
        system_prompt="You are a helpful assistant",
        cwd=Path("E:/ai-training-course/test"),
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits",
        model="claude-3-5-sonnet-20241022"
    )

    async for message in query(prompt="帮我在当前工作目录(E:/ai-training-course/test)创建一个fib.py文件。"
                                      "这个文件里面有一个计算斐波拉契数列的函数。"
                                      "这个函数需要使用一个速度很快的算法。"
                                      "请确保文件路径是 E:/ai-training-course/test/fib.py", options=options):
        print(message)


if __name__ == '__main__':
    anyio.run(main)
