<template>
  <div class="markdown-test">
    <h3>Markdown渲染测试</h3>
    
    <div class="test-content">
      <h4>测试内容：</h4>
      <textarea 
        v-model="testMarkdown" 
        rows="10" 
        cols="80"
        placeholder="输入Markdown内容进行测试..."
      ></textarea>
      
      <button @click="updateContent">更新内容</button>
      
      <h4>渲染结果：</h4>
      <div class="render-result">
        <XMarkdown
          :markdown="displayContent"
          :enable-latex="true"
          :enable-breaks="true"
          :allow-html="false"
          :themes="{
            light: 'vitesse-light',
            dark: 'vitesse-dark'
          }"
          :default-theme-mode="'light'"
          :need-view-code-btn="true"
          class="test-markdown-content"
        />
      </div>
      
      <h4>调试信息：</h4>
      <div class="debug-info">
        <p>内容长度: {{ displayContent.length }}</p>
        <p>行数: {{ displayContent.split('\n').length }}</p>
        <pre>{{ displayContent.substring(0, 500) }}{{ displayContent.length > 500 ? '...' : '' }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref} from 'vue';
import {XMarkdown} from 'vue-element-plus-x';

const testMarkdown = ref(`# Python冒泡排序算法测试

这是一个测试Markdown渲染的示例，包含完整的Python冒泡排序算法：

\`\`\`python
def bubble_sort(arr):
    """
    实现冒泡排序算法
    参数:
        arr (list): 需要排序的列表
    返回:
        list: 排序后的列表
    """
    n = len(arr)

    # 遍历所有数组元素
    for i in range(n):
        # 最后 i个元素已经是排序好的
        swapped = False
        for j in range(0, n-i-1):
            # 遍历数组从0 到 n-i-1
            # 如果当前元素大于下一个元素则交换它们
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
                swapped = True
        # 如果没有发生交换，提前结束
        if not swapped:
            break
    return arr

# 测试代码
if __name__ == "__main__":
    # 测试数据
    test_array = [64, 34, 25, 12, 22, 11, 90]
    print("排序前的数组:")
    print(test_array)

    # 调用冒泡排序函数
    sorted_array = bubble_sort(test_array)
    print("排序后的数组:")
    print(sorted_array)
\`\`\`

## 算法解释

1. **函数定义**：
   - \`bubble_sort(arr)\`：接受列表参数，返回排序后的列表

2. **外层循环**：
   - \`for i in range(n)\`：控制遍历轮数

3. **内层循环**：
   - \`for j in range(0, n-i-1)\`：比较和交换相邻元素

4. **优化**：
   - 使用 \`swapped\` 标志，如果一轮中没有交换，说明已排序完成

## 运行结果

\`\`\`
排序前的数组:
[64, 34, 25, 12, 22, 11, 90]
排序后的数组:
[11, 12, 22, 25, 34, 64, 90]
\`\`\`

## 算法解释

冒泡排序是一种简单的排序算法，它重复地遍历要排序的数列，一次比较两个元素，如果它们的顺序错误就把它们交换过来。

### 时间复杂度
- 最好情况：O(n)
- 平均情况：O(n²)
- 最坏情况：O(n²)

### 空间复杂度
O(1) - 原地排序算法
`);

const displayContent = ref(testMarkdown.value);

const updateContent = () => {
  displayContent.value = testMarkdown.value;
  console.log('更新内容，长度:', displayContent.value.length);
};
</script>

<style lang="scss" scoped>
.markdown-test {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;

  .test-content {
    margin-top: 20px;

    textarea {
      width: 100%;
      margin: 10px 0;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-family: monospace;
    }

    button {
      padding: 8px 16px;
      background: #409eff;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      margin: 10px 0;

      &:hover {
        background: #337ecc;
      }
    }

    .render-result {
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 20px;
      margin: 10px 0;
      background: #f9f9f9;
    }

    .debug-info {
      background: #f0f0f0;
      padding: 15px;
      border-radius: 4px;
      margin: 10px 0;

      pre {
        background: white;
        padding: 10px;
        border-radius: 4px;
        overflow-x: auto;
        font-size: 12px;
        line-height: 1.4;
      }
    }
  }
}

.test-markdown-content {
  // 代码块样式优化
  :deep(pre) {
    max-width: 100% !important;
    overflow-x: auto !important;
    white-space: pre !important;
    background-color: #f6f8fa !important;
    border: 1px solid #d0d7de !important;
    border-radius: 8px !important;
    padding: 16px !important;
    margin: 12px 0 !important;
    font-size: 13px !important;
    line-height: 1.45 !important;
    font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace !important;

    code {
      background: transparent !important;
      padding: 0 !important;
      border-radius: 0 !important;
      white-space: pre !important;
      word-wrap: normal !important;
    }
  }

  // 行内代码样式
  :deep(p code), :deep(li code) {
    background-color: rgba(175, 184, 193, 0.2) !important;
    padding: 2px 4px !important;
    border-radius: 4px !important;
    font-size: 0.9em !important;
    font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace !important;
  }
}
</style>
