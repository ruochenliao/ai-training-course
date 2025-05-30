### (二) Python 编程案例：打造你的“记忆永不消逝”的超级清单App！

还在用便利贴？太OUT啦！今天，咱们要用Python大神来打造一个命令行界面的“超级清单App”，不仅能帮你记住鸡毛蒜皮的小事，还能把它们刻进“数字石板”（保存到文件里），保证下次开机，它们还乖乖地在那儿等你！

1.  **秘密基地 (`todo_app_persistent.py`)**

    所有神秘代码，咱们都藏在这个叫做 `todo_app_persistent.py` 的文件里。够专一吧？

2.  **施展Python魔法 (`todo_app_persistent.py`)**

    ```python
    import json # 导入JSON魔法，让数据在文件和程序间自由穿梭
    import os   # 导入OS魔法，探查文件是否存在，就像侦探一样！

    DATA_FILE = "tasks.json" # 我们的“数字石板”就叫这个名儿！

    def load_tasks():
        """从“数字石板”上唤醒沉睡的任务们。"""
        if not os.path.exists(DATA_FILE):
            print("（悄悄话：你的石板还是全新的，一个字儿都没有！）")
            return [] # 石板是空的？那就从零开始呗！
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                tasks = json.load(f) # 念动咒语，把石板上的字变成Python看得懂的列表
            print("（任务们：我们回来啦！想我们了没？）")
            return tasks
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"警告：糟糕！{DATA_FILE} 石板好像被外星人加密了，或者根本找不到！只能给你个空列表先用着了。")
            return []

    def save_tasks(tasks):
        """把活蹦乱跳的任务们刻回到“数字石板”上。"""
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=4) # 施展JSON魔法，把任务列表变成石板上的精美刻印
            # print("（石板：搞定！所有任务都已安全备份，高枕无忧！）") # 想看保存提示？取消这行注释就行
        except IOError:
            print(f"错误：天呐！往 {DATA_FILE} 石板上刻字的时候，手滑了...保存失败！")

    def show_tasks(tasks):
        """向你展示所有待办的“小目标”。"""
        if not tasks:
            print("\n你的待办事项列表比我的钱包还干净！")
            return
        print("\n--- 你的宏伟蓝图（又名：待办事项） ---")
        for index, task in enumerate(tasks):
            status = "[✔]" if task.get("completed") else "[ ]" # 完成的打个勾，没完成的留个空，强迫症福音！
            priority_map = {1: "(十万火急!!!)", 2: "(有点急~)", 3: "(佛系随缘)", None: "(优先级？不存在的)"}
            priority_display = priority_map.get(task.get("priority"))
            print(f"{index + 1}. {status} {task['description']} {priority_display}")
        print("-------------------------------------")

    def add_task(tasks):
        """给你的“小目标”清单添砖加瓦。"""
        description = input("客官，想添加点啥新任务呀？请赐教：")
        if not description.strip():
            print("啥都不写可不行哦，任务描述不能为空白，不然我咋知道你要干啥？")
            return

        while True:
            try:
                priority_str = input("这事儿有多急？(1-十万火急, 2-有点急, 3-佛系随缘, 直接回车就表示‘我不关心优先级’): ")
                if not priority_str:
                    priority = None # 不输入？那就是“佛系青年”专属优先级
                    break
                priority = int(priority_str)
                if priority in [1, 2, 3]:
                    break
                else:
                    print("请输入1、2、3或者直接回车，别调皮捣蛋输别的数字哦！")
            except ValueError:
                print("优先级得是个数字啦，比如1，2，3这种，别输火星文哦！")

        tasks.append({"description": description, "completed": False, "priority": priority}) # 新任务诞生！
        print(f"\n搞定！任务 '{description}' 已经成功加入你的宏伟蓝图！")
        save_tasks(tasks) # 赶紧刻到石板上，免得忘了

    def mark_task_complete(tasks):
        """给完成的任务戴小红花，或者把后悔药给吃了（标记未完成）。"""
        show_tasks(tasks)
        if not tasks: return # 清单空空如也，还标记个啥？

        try:
            task_index_str = input("请翻牌子！要给哪个任务的状态来个乾坤大挪移？（输入序号）：")
            task_index = int(task_index_str) - 1 # Python世界的序号是从0开始的，咱们得换算一下
            if 0 <= task_index < len(tasks):
                tasks[task_index]["completed"] = not tasks[task_index]["completed"] # 状态反转，True变False，False变True，刺激！
                status_text = "已光荣完成" if tasks[task_index]["completed"] else "又回到起点（未完成）"
                print(f"\n任务 '{tasks[task_index]['description']}' 已成功切换到 {status_text} 状态！")
                save_tasks(tasks) # 状态变了，石板上的记录也得更新
            else:
                print("输入的序号好像不对哦，是不是手抖了？查无此任务。")
        except ValueError:
            print("请输入任务前面那个正经的数字序号，别开玩笑哈！")

    def edit_task(tasks):
        """给任务整容，或者调整它的江湖地位（优先级）。"""
        show_tasks(tasks)
        if not tasks: return # 没任务还编辑啥呀，洗洗睡吧

        try:
            task_index_str = input("想给哪个任务动动刀子？（输入序号）：")
            task_index = int(task_index_str) - 1
            if 0 <= task_index < len(tasks):
                current_task = tasks[task_index]
                print(f"\n当前任务描述：{current_task['description']}")
                new_description = input("请输入新的任务描述 (如果不想改，直接按回车就行)：")
                if new_description.strip(): # 如果输入了新描述（而且不是一堆空格）
                    current_task['description'] = new_description.strip()

                priority_map_display = {1: "十万火急!!!", 2: "有点急~", 3: "佛系随缘", None: "压根没优先级"}
                current_priority_display = priority_map_display.get(current_task.get("priority"))
                print(f"当前任务优先级：{current_priority_display}")
                while True:
                    try:
                        new_priority_str = input("要不要调整一下它的江湖地位？(1-十万火急, 2-有点急, 3-佛系随缘, 0-取消优先级, 直接回车保持不变): ")
                        if not new_priority_str: # 不想改？那就这样吧
                            break
                        if new_priority_str == '0': # 输入0，就是想让它四大皆空，没有优先级
                            current_task['priority'] = None
                            break
                        new_priority = int(new_priority_str)
                        if new_priority in [1, 2, 3]:
                            current_task['priority'] = new_priority
                            break
                        else:
                            print("请输入0、1、2、3或者直接回车，别乱来哦！")
                    except ValueError:
                        print("优先级得是个数字啦，比如0, 1, 2, 3这种，别闹！")
                
                print(f"\n任务 '{current_task['description']}' 已经焕然一新！")
                save_tasks(tasks) # 整容完毕，赶紧更新石板记录
            else:
                print("输入的序号好像不对劲，找不到这个任务呀。")
        except ValueError:
            print("请输入任务前面那个正经的数字序号，拜托拜托！")

    def remove_task(tasks):
        """有些任务，完成了它的历史使命，就让它随风而去吧..."""
        show_tasks(tasks)
        if not tasks: return # 都空了还删啥？

        try:
            task_index_str = input("狠心抛弃哪个任务？（输入序号）：")
            task_index = int(task_index_str) - 1
            if 0 <= task_index < len(tasks):
                removed_task = tasks.pop(task_index) # “啪”，任务消失了！
                print(f"\n任务 '{removed_task['description']}' 已被你无情抛弃，再见了您内！")
                save_tasks(tasks) # 石板上的也得擦掉
            else:
                print("序号输错啦，这个任务它不存在于这个次元。")
        except ValueError:
            print("请输入任务前面那个正经的数字序号，OK？")

    def main_menu(tasks):
        """欢迎来到“超级清单App”的指挥中心！"""
        while True:
            print("\n========== 超级清单App指挥中心 ==========")
            print("1. 偷看一下我的所有小目标")
            print("2. 立个新Flag (添加新事项)")
            print("3. 给任务盖章 (标记/取消标记完成)")
            print("4. 给任务整容 (编辑事项)")
            print("5. 断舍离 (移除事项)")
            print("6. 溜了溜了 (退出)")
            print("=========================================")

            choice = input("请指示 (输入1-6中的一个数字，按回车确认)：")

            if choice == '1':
                show_tasks(tasks)
            elif choice == '2':
                add_task(tasks)
            elif choice == '3':
                mark_task_complete(tasks)
            elif choice == '4':
                edit_task(tasks)
            elif choice == '5':
                remove_task(tasks)
            elif choice == '6':
                print("\n感谢您的宠幸！任务已妥善保管，下次再见么么哒！")
                break
            else:
                print("\n客官，您输入的指令好像有点跑偏，请输入1到6之间的数字哦！")

    if __name__ == "__main__": # 程序入口，就像电影开场一样
        tasks_list = load_tasks() # 电影开始前，先把上次的剧情（任务）回忆一下
        main_menu(tasks_list)   # 正片开始！进入指挥中心
    ```

    **代码“人话”翻译**：
    *   `import json` & `import os`：请来了两位魔法师，一个管数据变形（JSON），一个管探路（OS）。
    *   `DATA_FILE = "tasks.json"`：给我们的“数字石板”取了个响亮的名字。
    *   `load_tasks()`：这个函数负责在程序启动时，偷偷摸摸地去检查石板上有没有刻着上次的任务。有就读出来，没有就耸耸肩，告诉你“啥也没有”。
    *   `save_tasks(tasks)`：每次你对任务列表做了修改（添加、删除、打勾勾），这个函数就会像个勤劳的小蜜蜂，把最新的任务列表重新刻到石板上，保证万无一失。
    *   `show_tasks(tasks)`：想看看你都给自己挖了哪些坑（划掉）定了哪些小目标？这个函数会把它们漂漂亮亮地展示出来，完成的还会给你个小勾勾✔，优先级也给你标得明明白白。
    *   `add_task(tasks)`：灵感来了，想加个新任务？这个函数会热情地问你任务是啥，急不急，然后“嗖”地一下加到你的清单里，并立刻存盘。
    *   `mark_task_complete(tasks)`：某个任务光荣完成了？或者手滑点错了想反悔？这个函数帮你轻松切换任务的完成状态，已完成 <-> 未完成，so easy！
    *   `edit_task(tasks)`：任务描述写错了？或者事情的紧急程度变了？用这个函数给你的任务来个“微整形”，改描述、调优先级，随你喜欢。
    *   `remove_task(tasks)`：有些任务完成了它的使命，或者你单纯不想要它了，这个函数帮你“断舍离”，把它从清单里彻底移除。
    *   `main_menu(tasks)`：这是我们App的“大脑中枢”，一个无限循环的菜单，你可以在这里发号施令，选择要进行的操作。
    *   `if __name__ == "__main__":`：这是Python程序的“启动按钮”。一点火，程序就先加载旧任务，然后把你带到主菜单开始玩耍。

3.  **开机！启动！测试！**
    *   在你的Trae IDE里，找到 `todo_app_persistent.py` 这个文件，深吸一口气，然后优雅地打开它。
    *   看到IDE右上角那个像火箭一样的“运行”按钮了吗？点它！或者，如果你是命令行高手，也可以在Trae IDE的集成终端里输入 `python todo_app_persistent.py` 然后潇洒地按下回车。
    *   **第一次亲密接触**：因为 `tasks.json` 这个“数字石板”一开始是不存在的（除非你偷偷创建了它），所以程序会告诉你，你的清单是空的，就像新买的记事本一样干净。
    *   **疯狂操作猛如虎**：
        *   选 `2. 立个新Flag`，随便输入点啥，比如“中午吃顿好的”，“学习Python三小时（然后玩一整天）”，再给它们定个优先级。
        *   选 `1. 偷看一下我的所有小目标`，看看你刚才立的Flag是不是都乖乖躺在列表里了。
        *   选 `3. 给任务盖章`，挑一个任务，把它标记成“已光荣完成”。再回去看看，是不是多了个小勾勾？
        *   选 `4. 给任务整容`，找个任务，给它改个更酷的名字，或者调整一下它的“江湖地位”（优先级）。
        *   选 `5. 断舍离`，忍痛割爱，删掉一个任务。
        *   心满意足了？选 `6. 溜了溜了`，程序会跟你说拜拜。
    *   **见证奇迹的时刻（持久化测试）**：
        *   再次运行 `python todo_app_persistent.py` 命令。
        *   迫不及待地选 `1. 偷看一下我的所有小目标`。Duang！上次你退出前辛辛苦苦添加、修改、标记的任务们，是不是都原封不动地回来了？这就是“记忆永不消逝”的魔力！数据持久化，成了！
        *   不信？你还可以在你的文件管理器里找到那个 `tasks.json` 文件，用文本编辑器打开它，你会看到一堆像天书一样的JSON代码，那就是你所有任务的“灵魂”所在！