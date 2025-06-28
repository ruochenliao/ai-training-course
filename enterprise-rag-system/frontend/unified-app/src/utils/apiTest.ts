/**
 * API接口测试和联调工具
 * 用于验证前后端接口的连通性和数据格式
 */

import { apiClient } from './api';
import { message } from 'antd';

export interface TestResult {
  endpoint: string;
  method: string;
  success: boolean;
  responseTime: number;
  error?: string;
  data?: any;
}

export class ApiTester {
  private results: TestResult[] = [];

  /**
   * 测试认证相关接口
   */
  async testAuthEndpoints(): Promise<TestResult[]> {
    const authTests: TestResult[] = [];

    // 测试系统健康检查
    authTests.push(await this.testEndpoint(
      'GET /health',
      () => apiClient.getSystemHealth()
    ));

    // 测试系统信息
    authTests.push(await this.testEndpoint(
      'GET /api/v1/system/info',
      () => apiClient.getSystemInfo()
    ));

    // 测试API信息
    authTests.push(await this.testEndpoint(
      'GET /api/v1/',
      () => apiClient.get('/api/v1/')
    ));

    return authTests;
  }

  /**
   * 测试用户认证流程
   */
  async testUserAuth(username: string, password: string): Promise<TestResult[]> {
    const authTests: TestResult[] = [];

    // 测试登录
    authTests.push(await this.testEndpoint(
      'POST /api/v1/auth/login',
      () => apiClient.login(username, password)
    ));

    // 如果登录成功，测试获取用户信息
    const loginResult = authTests[authTests.length - 1];
    if (loginResult.success && loginResult.data?.access_token) {
      apiClient.setToken(loginResult.data.access_token);

      authTests.push(await this.testEndpoint(
        'GET /api/v1/auth/me',
        () => apiClient.getCurrentUser()
      ));
    }

    return authTests;
  }

  /**
   * 测试知识库相关接口
   */
  async testKnowledgeBaseEndpoints(): Promise<TestResult[]> {
    const kbTests: TestResult[] = [];

    // 测试获取知识库列表
    kbTests.push(await this.testEndpoint(
      'GET /api/v1/knowledge-bases/',
      () => apiClient.getKnowledgeBases({ page: 1, size: 10 })
    ));

    // 测试创建知识库
    kbTests.push(await this.testEndpoint(
      'POST /api/v1/knowledge-bases/',
      () => apiClient.createKnowledgeBase({
        name: `测试知识库_${Date.now()}`,
        description: '这是一个测试知识库',
        knowledge_type: 'general',
        visibility: 'private'
      })
    ));

    return kbTests;
  }

  /**
   * 测试文档管理接口
   */
  async testDocumentEndpoints(): Promise<TestResult[]> {
    const docTests: TestResult[] = [];

    // 测试获取文档列表
    docTests.push(await this.testEndpoint(
      'GET /api/v1/documents/',
      () => apiClient.getDocuments({ page: 1, size: 10 })
    ));

    return docTests;
  }

  /**
   * 测试搜索接口
   */
  async testSearchEndpoints(): Promise<TestResult[]> {
    const searchTests: TestResult[] = [];

    const testQuery = '测试查询';

    // 测试向量搜索
    searchTests.push(await this.testEndpoint(
      'POST /api/v1/search/vector',
      () => apiClient.vectorSearch({
        query: testQuery,
        top_k: 5
      })
    ));

    // 测试图谱搜索
    searchTests.push(await this.testEndpoint(
      'POST /api/v1/search/graph',
      () => apiClient.graphSearch({
        query: testQuery,
        top_k: 5
      })
    ));

    // 测试混合搜索
    searchTests.push(await this.testEndpoint(
      'POST /api/v1/search/hybrid',
      () => apiClient.hybridSearch({
        query: testQuery,
        top_k: 5
      })
    ));

    return searchTests;
  }

  /**
   * 测试聊天接口
   */
  async testChatEndpoints(): Promise<TestResult[]> {
    const chatTests: TestResult[] = [];

    // 测试获取对话列表
    chatTests.push(await this.testEndpoint(
      'GET /api/v1/conversations/',
      () => apiClient.getConversations({ page: 1, size: 10 })
    ));

    // 测试发送消息
    chatTests.push(await this.testEndpoint(
      'POST /api/v1/chat/',
      () => apiClient.sendChatMessage({
        message: '你好，这是一个测试消息',
        temperature: 0.7,
        max_tokens: 1000
      })
    ));

    return chatTests;
  }

  /**
   * 执行完整的接口测试套件
   */
  async runFullTestSuite(credentials?: { username: string; password: string }): Promise<TestResult[]> {
    const allResults: TestResult[] = [];

    try {
      // 1. 测试基础接口
      console.log('🔍 测试基础接口...');
      const basicTests = await this.testAuthEndpoints();
      allResults.push(...basicTests);

      // 2. 如果提供了凭据，测试认证流程
      if (credentials) {
        console.log('🔐 测试用户认证...');
        const authTests = await this.testUserAuth(credentials.username, credentials.password);
        allResults.push(...authTests);

        // 如果认证成功，继续测试其他接口
        const authSuccess = authTests.some(test => test.endpoint.includes('login') && test.success);
        if (authSuccess) {
          console.log('📚 测试知识库接口...');
          const kbTests = await this.testKnowledgeBaseEndpoints();
          allResults.push(...kbTests);

          console.log('📄 测试文档接口...');
          const docTests = await this.testDocumentEndpoints();
          allResults.push(...docTests);

          console.log('🔍 测试搜索接口...');
          const searchTests = await this.testSearchEndpoints();
          allResults.push(...searchTests);

          console.log('💬 测试聊天接口...');
          const chatTests = await this.testChatEndpoints();
          allResults.push(...chatTests);
        }
      }

      // 显示测试结果摘要
      this.showTestSummary(allResults);

    } catch (error) {
      console.error('测试套件执行失败:', error);
      message.error('测试套件执行失败');
    }

    return allResults;
  }

  /**
   * 测试单个接口端点
   */
  private async testEndpoint(
    name: string,
    testFunction: () => Promise<any>
  ): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      const data = await testFunction();
      const responseTime = Date.now() - startTime;
      
      console.log(`✅ ${name} - ${responseTime}ms`);
      
      return {
        endpoint: name,
        method: name.split(' ')[0],
        success: true,
        responseTime,
        data
      };
    } catch (error: any) {
      const responseTime = Date.now() - startTime;
      
      console.error(`❌ ${name} - ${responseTime}ms - ${error.message}`);
      
      return {
        endpoint: name,
        method: name.split(' ')[0],
        success: false,
        responseTime,
        error: error.message
      };
    }
  }

  /**
   * 显示测试结果摘要
   */
  private showTestSummary(results: TestResult[]): void {
    const total = results.length;
    const successful = results.filter(r => r.success).length;
    const failed = total - successful;
    const avgResponseTime = results.reduce((sum, r) => sum + r.responseTime, 0) / total;

    console.log('\n📊 测试结果摘要:');
    console.log(`总计: ${total} 个接口`);
    console.log(`成功: ${successful} 个`);
    console.log(`失败: ${failed} 个`);
    console.log(`平均响应时间: ${avgResponseTime.toFixed(2)}ms`);
    console.log(`成功率: ${((successful / total) * 100).toFixed(1)}%`);

    if (failed > 0) {
      console.log('\n❌ 失败的接口:');
      results.filter(r => !r.success).forEach(r => {
        console.log(`  - ${r.endpoint}: ${r.error}`);
      });
    }

    // 显示消息提示
    if (successful === total) {
      message.success(`所有 ${total} 个接口测试通过！`);
    } else {
      message.warning(`${successful}/${total} 个接口测试通过`);
    }
  }

  /**
   * 获取测试结果
   */
  getResults(): TestResult[] {
    return this.results;
  }

  /**
   * 清除测试结果
   */
  clearResults(): void {
    this.results = [];
  }
}

// 创建全局测试实例
export const apiTester = new ApiTester();

// 导出便捷测试函数
export const quickTest = {
  // 快速测试基础连接
  async basic(): Promise<boolean> {
    try {
      await apiClient.getSystemHealth();
      return true;
    } catch {
      return false;
    }
  },

  // 快速测试认证
  async auth(username: string, password: string): Promise<boolean> {
    try {
      const result = await apiClient.login(username, password);
      return !!result.access_token;
    } catch {
      return false;
    }
  },

  // 快速测试API可用性
  async api(): Promise<{ available: number; total: number }> {
    const endpoints = [
      () => apiClient.getSystemHealth(),
      () => apiClient.getSystemInfo(),
      () => apiClient.get('/api/v1/'),
    ];

    let available = 0;
    for (const endpoint of endpoints) {
      try {
        await endpoint();
        available++;
      } catch {
        // 忽略错误
      }
    }

    return { available, total: endpoints.length };
  }
};
