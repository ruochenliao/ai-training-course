class BankAccount:
    """
    银行账户基类
    包含账户名和余额属性，提供存款和取款功能
    """
    
    def __init__(self, account_name, initial_balance=0):
        """
        初始化银行账户
        
        Args:
            account_name (str): 账户名
            initial_balance (float): 初始余额，默认为0
        """
        self.account_name = account_name
        self.balance = initial_balance
    
    def deposit(self, amount):
        """
        存款方法
        
        Args:
            amount (float): 存款金额
        
        Returns:
            bool: 存款是否成功
        """
        if amount <= 0:
            print(f"❌ 存款失败：存款金额必须大于0，当前输入金额：{amount}")
            return False
        
        self.balance += amount
        print(f"✅ 存款成功：存入 {amount:.2f} 元，当前余额：{self.balance:.2f} 元")
        return True
    
    def withdraw(self, amount):
        """
        取款方法
        
        Args:
            amount (float): 取款金额
        
        Returns:
            bool: 取款是否成功
        """
        if amount <= 0:
            print(f"❌ 取款失败：取款金额必须大于0，当前输入金额：{amount}")
            return False
        
        if amount > self.balance:
            print(f"❌ 取款失败：余额不足，当前余额：{self.balance:.2f} 元，尝试取款：{amount:.2f} 元")
            return False
        
        self.balance -= amount
        print(f"✅ 取款成功：取出 {amount:.2f} 元，当前余额：{self.balance:.2f} 元")
        return True
    
    def get_balance(self):
        """
        获取当前余额
        
        Returns:
            float: 当前余额
        """
        return self.balance
    
    def __str__(self):
        """
        格式化账户信息
        
        Returns:
            str: 格式化的账户信息字符串
        """
        return f"账户名：{self.account_name}，余额：{self.balance:.2f} 元"


class SavingsAccount(BankAccount):
    """
    储蓄账户类，继承自BankAccount
    添加利息率属性和计算利息功能
    """
    
    def __init__(self, account_name, initial_balance=0, interest_rate=0.03):
        """
        初始化储蓄账户
        
        Args:
            account_name (str): 账户名
            initial_balance (float): 初始余额，默认为0
            interest_rate (float): 年利息率，默认为3%
        """
        # 调用父类构造函数
        super().__init__(account_name, initial_balance)
        self.interest_rate = interest_rate
    
    def add_interest(self):
        """
        添加利息到账户余额
        利息 = 当前余额 × 利息率
        
        Returns:
            float: 添加的利息金额
        """
        interest_amount = self.balance * self.interest_rate
        self.balance += interest_amount
        print(f"💰 利息计算：按 {self.interest_rate*100:.1f}% 年利率计算，获得利息 {interest_amount:.2f} 元")
        print(f"✅ 利息已添加到账户，当前余额：{self.balance:.2f} 元")
        return interest_amount
    
    def set_interest_rate(self, new_rate):
        """
        设置新的利息率
        
        Args:
            new_rate (float): 新的利息率
        
        Returns:
            bool: 设置是否成功
        """
        if new_rate < 0:
            print(f"❌ 设置失败：利息率不能为负数，当前输入：{new_rate}")
            return False
        
        old_rate = self.interest_rate
        self.interest_rate = new_rate
        print(f"✅ 利息率更新：从 {old_rate*100:.1f}% 更新为 {new_rate*100:.1f}%")
        return True
    
    def __str__(self):
        """
        重写父类的__str__方法，添加利息率信息
        
        Returns:
            str: 格式化的储蓄账户信息字符串
        """
        return f"储蓄账户 - 账户名：{self.account_name}，余额：{self.balance:.2f} 元，年利率：{self.interest_rate*100:.1f}%"


def test_bank_accounts():
    """
    测试银行账户系统的各种功能
    """
    print("🏦 银行账户系统测试")
    print("="*60)
    
    # 测试普通银行账户
    print("\n📋 测试1：普通银行账户功能")
    print("-"*40)
    
    # 创建普通账户
    account1 = BankAccount("张三", 1000)
    print(f"创建账户：{account1}")
    
    # 测试存款
    account1.deposit(500)
    account1.deposit(-100)  # 测试错误情况
    
    # 测试取款
    account1.withdraw(200)
    account1.withdraw(2000)  # 测试余额不足
    account1.withdraw(-50)   # 测试错误情况
    
    print(f"最终状态：{account1}")
    
    # 测试储蓄账户
    print("\n💰 测试2：储蓄账户功能")
    print("-"*40)
    
    # 创建储蓄账户
    savings1 = SavingsAccount("李四", 2000, 0.05)  # 5%年利率
    print(f"创建储蓄账户：{savings1}")
    
    # 测试继承的存取款功能
    savings1.deposit(1000)
    savings1.withdraw(500)
    
    # 测试利息计算
    savings1.add_interest()
    
    # 测试利息率设置
    savings1.set_interest_rate(0.04)  # 改为4%
    savings1.set_interest_rate(-0.01)  # 测试错误情况
    
    print(f"最终状态：{savings1}")
    
    # 测试多个账户
    print("\n👥 测试3：多账户管理")
    print("-"*40)
    
    accounts = [
        BankAccount("王五", 800),
        SavingsAccount("赵六", 1500, 0.035),
        SavingsAccount("孙七", 3000, 0.045)
    ]
    
    print("所有账户信息：")
    for i, account in enumerate(accounts, 1):
        print(f"{i}. {account}")
    
    # 为储蓄账户添加利息
    print("\n为储蓄账户添加利息：")
    for account in accounts:
        if isinstance(account, SavingsAccount):
            account.add_interest()
    
    print("\n添加利息后的账户信息：")
    for i, account in enumerate(accounts, 1):
        print(f"{i}. {account}")
    
    # 计算总资产
    total_balance = sum(account.get_balance() for account in accounts)
    print(f"\n💼 总资产：{total_balance:.2f} 元")
    
    print("\n" + "="*60)
    print("🎉 银行账户系统测试完成！")


def interactive_demo():
    """
    交互式演示程序
    """
    print("🏦 银行账户系统交互演示")
    print("="*50)
    
    accounts = {}
    
    while True:
        print("\n请选择操作：")
        print("1. 创建普通账户")
        print("2. 创建储蓄账户")
        print("3. 存款")
        print("4. 取款")
        print("5. 查看账户信息")
        print("6. 计算利息（仅储蓄账户）")
        print("7. 查看所有账户")
        print("8. 退出")
        
        choice = input("请输入选项 (1-8): ").strip()
        
        if choice == '1':
            name = input("请输入账户名: ").strip()
            try:
                balance = float(input("请输入初始余额: "))
                accounts[name] = BankAccount(name, balance)
                print(f"✅ 普通账户创建成功：{accounts[name]}")
            except ValueError:
                print("❌ 错误：请输入有效的数字")
        
        elif choice == '2':
            name = input("请输入账户名: ").strip()
            try:
                balance = float(input("请输入初始余额: "))
                rate = float(input("请输入年利率 (例如0.03表示3%): "))
                accounts[name] = SavingsAccount(name, balance, rate)
                print(f"✅ 储蓄账户创建成功：{accounts[name]}")
            except ValueError:
                print("❌ 错误：请输入有效的数字")
        
        elif choice == '3':
            name = input("请输入账户名: ").strip()
            if name in accounts:
                try:
                    amount = float(input("请输入存款金额: "))
                    accounts[name].deposit(amount)
                except ValueError:
                    print("❌ 错误：请输入有效的数字")
            else:
                print("❌ 错误：账户不存在")
        
        elif choice == '4':
            name = input("请输入账户名: ").strip()
            if name in accounts:
                try:
                    amount = float(input("请输入取款金额: "))
                    accounts[name].withdraw(amount)
                except ValueError:
                    print("❌ 错误：请输入有效的数字")
            else:
                print("❌ 错误：账户不存在")
        
        elif choice == '5':
            name = input("请输入账户名: ").strip()
            if name in accounts:
                print(f"账户信息：{accounts[name]}")
            else:
                print("❌ 错误：账户不存在")
        
        elif choice == '6':
            name = input("请输入储蓄账户名: ").strip()
            if name in accounts:
                if isinstance(accounts[name], SavingsAccount):
                    accounts[name].add_interest()
                else:
                    print("❌ 错误：该账户不是储蓄账户")
            else:
                print("❌ 错误：账户不存在")
        
        elif choice == '7':
            if accounts:
                print("\n所有账户信息：")
                for i, (name, account) in enumerate(accounts.items(), 1):
                    print(f"{i}. {account}")
                total = sum(account.get_balance() for account in accounts.values())
                print(f"\n💼 总资产：{total:.2f} 元")
            else:
                print("暂无账户")
        
        elif choice == '8':
            print("👋 感谢使用银行账户系统，再见！")
            break
        
        else:
            print("❌ 错误：请输入有效的选项 (1-8)")


if __name__ == "__main__":
    # 运行测试
    test_bank_accounts()
    
    # 询问是否运行交互演示
    print("\n是否运行交互演示？(y/n): ", end="")
    if input().lower().strip() in ['y', 'yes', '是', '好']:
        interactive_demo()