import queue
import random
import threading
import time
from datetime import datetime


class MultiThreadTaskProcessor:
    """
    多线程任务处理系统
    
    使用队列和多线程实现高效的任务处理，支持任务分发、结果收集和优雅停止。
    """
    
    def __init__(self, num_workers: int = 4):
        """
        初始化多线程任务处理器
        
        Args:
            num_workers (int): 工作线程数量，默认为4
        """
        self.num_workers = num_workers
        self.task_queue = queue.Queue()  # 任务队列
        self.result_queue = queue.Queue()  # 结果队列
        self.workers = []  # 工作线程列表
        self.is_running = False  # 运行状态标志
        self.task_count = 0  # 任务计数器
        self.completed_tasks = 0  # 完成任务计数器
        self.start_time = None  # 开始时间
        
        print(f"🚀 多线程任务处理器初始化完成")
        print(f"📊 配置信息：")
        print(f"   • 工作线程数量: {self.num_workers}")
        print(f"   • 任务队列: 已创建")
        print(f"   • 结果队列: 已创建")
    
    def worker(self, worker_id: int):
        """
        工作线程函数
        
        从任务队列获取任务，处理后将结果放入结果队列。
        接收到None信号时优雅退出。
        
        Args:
            worker_id (int): 工作线程ID
        """
        print(f"🔧 工作线程 {worker_id} 启动")
        
        while True:
            try:
                # 从任务队列获取任务
                task = self.task_queue.get()
                
                # 检查停止信号
                if task is None:
                    print(f"🛑 工作线程 {worker_id} 接收到停止信号，正在退出...")
                    self.task_queue.task_done()
                    break
                
                # 处理任务
                print(f"⚡ 工作线程 {worker_id} 开始处理任务: {task}")
                
                # 模拟耗时操作
                processing_time = random.uniform(1, 3)  # 随机1-3秒的处理时间
                time.sleep(processing_time)
                
                # 生成处理结果
                result = {
                    'task_id': task['id'],
                    'task_data': task['data'],
                    'worker_id': worker_id,
                    'processing_time': round(processing_time, 2),
                    'result': f"处理结果_{task['id']}",
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'status': 'completed'
                }
                
                # 将结果放入结果队列
                self.result_queue.put(result)
                
                # 更新完成计数
                self.completed_tasks += 1
                
                print(f"✅ 工作线程 {worker_id} 完成任务 {task['id']}，耗时 {processing_time:.2f}秒")
                
                # 标记任务完成
                self.task_queue.task_done()
                
            except Exception as e:
                print(f"❌ 工作线程 {worker_id} 处理任务时发生错误: {e}")
                # 即使出错也要标记任务完成
                self.task_queue.task_done()
        
        print(f"🏁 工作线程 {worker_id} 已退出")
    
    def start_workers(self):
        """
        启动所有工作线程
        """
        print(f"\n🚀 启动 {self.num_workers} 个工作线程...")
        
        self.is_running = True
        self.start_time = time.time()
        
        for i in range(self.num_workers):
            worker_thread = threading.Thread(
                target=self.worker,
                args=(i + 1,),
                name=f"Worker-{i + 1}"
            )
            worker_thread.daemon = True  # 设置为守护线程
            worker_thread.start()
            self.workers.append(worker_thread)
        
        print(f"✅ 所有工作线程启动完成")
    
    def add_tasks(self, num_tasks: int = 10):
        """
        向任务队列添加任务
        
        Args:
            num_tasks (int): 要添加的任务数量
        """
        print(f"\n📝 向任务队列添加 {num_tasks} 个任务...")
        
        for i in range(1, num_tasks + 1):
            task = {
                'id': i,
                'data': f"任务数据_{i}",
                'priority': random.choice(['high', 'medium', 'low']),
                'created_time': datetime.now().strftime('%H:%M:%S')
            }
            
            self.task_queue.put(task)
            self.task_count += 1
            
            print(f"📋 添加任务 {i}: {task['data']} (优先级: {task['priority']})")
        
        print(f"✅ 成功添加 {num_tasks} 个任务到队列")
        print(f"📊 当前队列状态：")
        print(f"   • 任务队列大小: {self.task_queue.qsize()}")
        print(f"   • 总任务数: {self.task_count}")
    
    def wait_for_completion(self):
        """
        等待所有任务完成
        
        使用task_queue.join()方法等待所有任务处理完成。
        """
        print(f"\n⏳ 等待所有任务完成...")
        print(f"📊 实时进度监控：")
        
        # 启动进度监控线程
        progress_thread = threading.Thread(target=self._monitor_progress)
        progress_thread.daemon = True
        progress_thread.start()
        
        # 等待所有任务完成
        self.task_queue.join()
        
        print(f"\n🎉 所有任务处理完成！")
        
        # 计算总耗时
        total_time = time.time() - self.start_time
        print(f"📈 处理统计：")
        print(f"   • 总任务数: {self.task_count}")
        print(f"   • 完成任务数: {self.completed_tasks}")
        print(f"   • 总耗时: {total_time:.2f}秒")
        print(f"   • 平均每任务耗时: {total_time/self.task_count:.2f}秒")
        print(f"   • 任务处理速率: {self.task_count/total_time:.2f}任务/秒")
    
    def _monitor_progress(self):
        """
        监控任务处理进度
        """
        while self.completed_tasks < self.task_count:
            progress = (self.completed_tasks / self.task_count) * 100
            remaining = self.task_count - self.completed_tasks
            
            print(f"📊 进度: {progress:.1f}% ({self.completed_tasks}/{self.task_count}) - 剩余: {remaining}")
            
            time.sleep(2)  # 每2秒更新一次进度
    
    def stop_workers(self):
        """
        优雅停止所有工作线程
        
        向每个工作线程发送None信号，让它们优雅退出。
        """
        print(f"\n🛑 开始停止工作线程...")
        
        # 向每个工作线程发送停止信号
        for i in range(self.num_workers):
            self.task_queue.put(None)
            print(f"📤 向工作线程 {i + 1} 发送停止信号")
        
        # 等待所有工作线程结束
        print(f"⏳ 等待工作线程退出...")
        for i, worker in enumerate(self.workers):
            worker.join(timeout=5)  # 最多等待5秒
            if worker.is_alive():
                print(f"⚠️ 工作线程 {i + 1} 未能在5秒内退出")
            else:
                print(f"✅ 工作线程 {i + 1} 已成功退出")
        
        self.is_running = False
        print(f"🏁 所有工作线程已停止")
    
    def collect_results(self) -> list:
        """
        收集所有处理结果
        
        Returns:
            list: 包含所有处理结果的列表
        """
        print(f"\n📥 收集处理结果...")
        
        results = []
        
        # 从结果队列中获取所有结果
        while not self.result_queue.empty():
            try:
                result = self.result_queue.get_nowait()
                results.append(result)
            except queue.Empty:
                break
        
        print(f"📊 结果收集完成，共收集到 {len(results)} 个结果")
        
        return results
    
    def display_results(self, results: list):
        """
        美观地显示处理结果
        
        Args:
            results (list): 处理结果列表
        """
        if not results:
            print(f"📭 没有找到任何处理结果")
            return
        
        print(f"\n" + "="*80)
        print(f"📋 任务处理结果详情")
        print(f"="*80)
        
        # 按任务ID排序
        results.sort(key=lambda x: x['task_id'])
        
        print(f"{'任务ID':<8} {'工作线程':<10} {'处理时间':<10} {'完成时间':<10} {'状态':<10} {'结果':<20}")
        print("-"*80)
        
        total_processing_time = 0
        worker_stats = {}
        
        for result in results:
            task_id = result['task_id']
            worker_id = result['worker_id']
            processing_time = result['processing_time']
            timestamp = result['timestamp']
            status = result['status']
            result_data = result['result']
            
            print(f"{task_id:<8} {worker_id:<10} {processing_time:<10} {timestamp:<10} {status:<10} {result_data:<20}")
            
            # 统计信息
            total_processing_time += processing_time
            if worker_id not in worker_stats:
                worker_stats[worker_id] = {'count': 0, 'time': 0}
            worker_stats[worker_id]['count'] += 1
            worker_stats[worker_id]['time'] += processing_time
        
        print("-"*80)
        
        # 显示统计信息
        print(f"\n📈 处理统计分析：")
        print(f"   • 总处理时间: {total_processing_time:.2f}秒")
        print(f"   • 平均处理时间: {total_processing_time/len(results):.2f}秒/任务")
        
        print(f"\n👥 工作线程统计：")
        for worker_id, stats in worker_stats.items():
            avg_time = stats['time'] / stats['count']
            print(f"   • 工作线程 {worker_id}: 处理 {stats['count']} 个任务，总耗时 {stats['time']:.2f}秒，平均 {avg_time:.2f}秒/任务")
    
    def demonstrate_queue_operations(self):
        """
        演示队列操作的核心特性
        """
        print(f"\n" + "="*70)
        print(f"🎓 多线程队列操作技术演示")
        print(f"="*70)
        
        print(f"\n🔍 队列操作核心特性：")
        print(f"\n📊 Queue.Queue 特性：")
        print(f"   ✅ 线程安全：多个线程可以安全地同时访问")
        print(f"   ✅ 阻塞操作：get()方法会等待直到有数据可用")
        print(f"   ✅ 任务跟踪：task_done()和join()实现任务同步")
        print(f"   ✅ 容量控制：可以设置最大容量防止内存溢出")
        
        print(f"\n🚀 多线程优势：")
        print(f"   ⚡ 并发处理：多个任务同时执行，提高效率")
        print(f"   🔄 负载均衡：任务自动分配给空闲线程")
        print(f"   💾 内存高效：队列控制内存使用，避免溢出")
        print(f"   🛡️ 异常隔离：单个线程异常不影响其他线程")
        
        print(f"\n🛠️ 关键方法说明：")
        print(f"   📤 put(item): 将任务放入队列")
        print(f"   📥 get(): 从队列获取任务（阻塞）")
        print(f"   ✅ task_done(): 标记任务完成")
        print(f"   ⏳ join(): 等待所有任务完成")
        print(f"   📊 qsize(): 获取队列当前大小")
        print(f"   🔍 empty(): 检查队列是否为空")
        
        print(f"\n🎯 适用场景：")
        print(f"   🌐 网络请求：并发处理HTTP请求")
        print(f"   📁 文件处理：批量处理文件操作")
        print(f"   🔢 数据计算：并行数值计算任务")
        print(f"   🖼️ 图像处理：批量图像转换和处理")
        print(f"   📊 数据分析：大数据集的并行分析")
        
        print(f"\n⚠️ 注意事项：")
        print(f"   🔒 GIL限制：Python的GIL限制CPU密集型任务的并行性")
        print(f"   💡 适合I/O密集型：网络、文件操作等I/O密集型任务效果最佳")
        print(f"   🧹 资源清理：确保线程优雅退出，避免资源泄露")
        print(f"   🛡️ 异常处理：每个线程都应有完善的异常处理机制")

def create_sample_tasks(num_tasks: int = 10) -> list:
    """
    创建示例任务列表
    
    Args:
        num_tasks (int): 任务数量
    
    Returns:
        list: 任务列表
    """
    tasks = []
    task_types = ['数据处理', '文件转换', '网络请求', '图像处理', '数据分析']
    
    for i in range(1, num_tasks + 1):
        task = {
            'id': i,
            'type': random.choice(task_types),
            'data': f"任务数据_{i}",
            'priority': random.choice(['high', 'medium', 'low']),
            'estimated_time': random.uniform(1, 3)
        }
        tasks.append(task)
    
    return tasks

def demonstrate_threading_concepts():
    """
    演示多线程核心概念
    """
    print(f"\n" + "="*70)
    print(f"🎓 Python多线程核心概念")
    print(f"="*70)
    
    print(f"\n🧵 线程基础概念：")
    print(f"   🔄 并发 vs 并行：")
    print(f"     • 并发：多个任务交替执行，看起来同时进行")
    print(f"     • 并行：多个任务真正同时执行（多核CPU）")
    
    print(f"\n🔒 GIL (全局解释器锁)：")
    print(f"   • Python的GIL确保同一时间只有一个线程执行Python字节码")
    print(f"   • 对I/O密集型任务影响较小（I/O时会释放GIL）")
    print(f"   • 对CPU密集型任务影响较大（建议使用multiprocessing）")
    
    print(f"\n🎯 线程类型选择：")
    print(f"   ⚡ I/O密集型任务 → 多线程 (threading)")
    print(f"     • 网络请求、文件读写、数据库操作")
    print(f"   🔢 CPU密集型任务 → 多进程 (multiprocessing)")
    print(f"     • 数学计算、图像处理、数据分析")
    
    print(f"\n🛠️ 线程同步机制：")
    print(f"   🔐 Lock: 互斥锁，确保同一时间只有一个线程访问资源")
    print(f"   🎫 Semaphore: 信号量，控制同时访问资源的线程数量")
    print(f"   🚦 Condition: 条件变量，线程间的条件等待和通知")
    print(f"   🎯 Event: 事件对象，线程间的简单通信机制")
    
    print(f"\n📋 队列类型：")
    print(f"   📦 Queue: 先进先出队列")
    print(f"   📚 LifoQueue: 后进先出队列（栈）")
    print(f"   🏆 PriorityQueue: 优先级队列")

def main():
    """
    主函数：演示多线程任务处理系统的完整流程
    """
    print("="*80)
    print("🚀 Python多线程任务处理系统演示")
    print("="*80)
    
    try:
        # 步骤1：创建多线程任务处理器
        print("\n📋 步骤1：初始化多线程任务处理器")
        processor = MultiThreadTaskProcessor(num_workers=4)
        
        # 步骤2：启动工作线程
        print("\n📋 步骤2：启动工作线程")
        processor.start_workers()
        
        # 步骤3：添加任务到队列
        print("\n📋 步骤3：添加任务到队列")
        processor.add_tasks(num_tasks=10)
        
        # 步骤4：等待任务完成
        print("\n📋 步骤4：等待任务完成")
        processor.wait_for_completion()
        
        # 步骤5：收集和显示结果
        print("\n📋 步骤5：收集和显示结果")
        results = processor.collect_results()
        processor.display_results(results)
        
        # 步骤6：优雅停止工作线程
        print("\n📋 步骤6：优雅停止工作线程")
        processor.stop_workers()
        
        # 步骤7：技术概念演示
        print("\n📋 步骤7：技术概念演示")
        processor.demonstrate_queue_operations()
        demonstrate_threading_concepts()
        
        print(f"\n" + "="*80)
        print(f"🎯 核心技术要点总结：")
        print(f"• 多线程：使用threading模块创建和管理工作线程")
        print(f"• 队列操作：Queue.Queue实现线程安全的任务分发")
        print(f"• 线程同步：task_done()和join()方法实现任务同步")
        print(f"• 优雅停止：使用None信号优雅终止工作线程")
        print(f"• 异常处理：完善的错误捕获和处理机制")
        print(f"• 进度监控：实时显示任务处理进度和统计信息")
        print(f"="*80)
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 用户中断程序执行")
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🏁 多线程任务处理系统演示完成")

if __name__ == "__main__":
    main()