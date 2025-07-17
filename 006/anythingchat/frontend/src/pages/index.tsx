import {
  BookOpenText,
  FileText,
  Boxes,
  MessageCircle,
  ScanSearch,
  BarChart2,
  FileSearch,
  Users,
  Settings,
  PanelsTopLeft,
} from 'lucide-react';
import Image from 'next/image';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';

import R2RServerCard from '@/components/ChatDemo/ServerCard';
import Layout from '@/components/Layout';
import RequestsCard from '@/components/RequestsCard';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/Button';
import { CardTitle, CardHeader, CardContent, Card } from '@/components/ui/card';
import { brandingConfig } from '@/config/brandingConfig';
import { useUserContext } from '@/context/UserContext';

const HomePage = () => {
  const router = useRouter();
  const { isAuthenticated, isSuperUser, pipeline } = useUserContext();
  const [copied, setCopied] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (isAuthenticated && !isSuperUser()) {
      router.replace('/documents');
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <Layout includeFooter>
      <main className="w-full flex flex-col container h-screen-[calc(100%-4rem)]">
        <div className="relative bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 p-5 min-h-screen">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Left column - Alert */}
            <div className="w-full lg:w-2/3 flex flex-col gap-4">
              <Alert variant="default" className="flex flex-col modern-card animate-fade-in">
                <AlertTitle className="text-lg ">
                  <div className="flex gap-2 text-xl">
                    <span className="text-gray-500 dark:text-gray-200 font-semibold">
                      欢迎使用 {brandingConfig.deploymentName} 智能对话平台！
                    </span>
                  </div>
                </AlertTitle>
                <AlertDescription>
                  <p className="mb-4 text-sm text-gray-600 dark:text-gray-300">
                    在这里，您可以找到各种工具来帮助您管理智能对话系统，
                    并直接为用户部署面向用户的应用程序。
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="flex items-start space-x-3">
                      <FileText className="w-5 h-5 text-primary" />
                      <div>
                        <h3 className="text-sm font-semibold mb-1">
                          文档管理
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          上传、更新和删除文档及其元数据。
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <Boxes className="w-5 h-5 text-primary" />
                      <div>
                        <h3 className="text-sm font-semibold mb-1">
                          集合管理
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          管理和共享文档组，创建知识图谱。
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <MessageCircle className="w-5 h-5 text-primary" />
                      <div>
                        <h3 className="text-sm font-semibold mb-1">智能对话</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          生成智能对话响应。
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <ScanSearch className="w-5 h-5 text-primary" />
                      <div>
                        <h3 className="text-sm font-semibold mb-1">智能搜索</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          在您的文档和集合中进行搜索。
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <Users className="w-5 h-5 text-primary" />
                      <div>
                        <h3 className="text-sm font-semibold mb-1">用户管理</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          跟踪用户查询、搜索结果和AI响应。
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <FileSearch className="w-5 h-5 text-primary" />
                      <div>
                        <h3 className="text-sm font-semibold mb-1">日志记录</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          跟踪用户查询、搜索结果和AI响应。
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <BarChart2 className="w-5 h-5 text-primary" />
                      <div>
                        <h3 className="text-sm font-semibold mb-1">
                          数据分析
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          丰富的用户查询和交互分析洞察。
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <Settings className="w-5 h-5 text-primary" />
                      <div>
                        <h3 className="text-sm font-semibold mb-1">系统设置</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          管理您的 {brandingConfig.deploymentName} 部署
                          设置和配置。
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                    <div className="flex space-x-4">
                      <Button
                        className="flex items-center justify-center px-4 py-2 text-sm"
                        color="transparent"
                        onClick={() =>
                          window.open(
                            'https://github.com/AnythingChat/AnythingChat/issues/new?assignees=&labels=&projects=&template=feature_request.md&title=',
                            '_blank'
                          )
                        }
                      >
                        功能建议
                      </Button>
                      <Button
                        className="flex items-center justify-center px-4 py-2 text-sm"
                        color="transparent"
                        onClick={() =>
                          window.open(
                            'https://github.com/AnythingChat/AnythingChat/issues/new?assignees=&labels=&projects=&template=bug_report.md&title=',
                            '_blank'
                          )
                        }
                      >
                        问题反馈
                      </Button>
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
              {/* SDK Cards */}
              <div className="flex flex-col gap-4">
                <div className="flex flex-col sm:flex-row gap-4">
                  {brandingConfig.homePage.pythonSdk && (
                    <Card className="w-full sm:w-1/2 flex flex-col modern-card animate-fade-in">
                      <CardHeader className="flex flex-row items-center space-x-2">
                        <Image
                          src="/images/python-logo.svg"
                          alt="Python Logo"
                          width={30}
                          height={30}
                        />
                        <CardTitle>Python SDK</CardTitle>
                      </CardHeader>
                      <CardContent className="flex flex-col justify-end flex-grow">
                        <div className="flex flex-row space-x-2">
                          <Button
                            className="rounded-md py-1 px-3"
                            color="light"
                            onClick={() =>
                              window.open(
                                'https://r2r-docs.sciphi.ai/documentation/python-sdk/introduction',
                                '_blank'
                              )
                            }
                          >
                            <div className="flex items-center">
                              <BookOpenText size={20} className="mr-2" />
                              <span>文档</span>
                            </div>
                          </Button>
                          <Button
                            className="rounded-md py-1 px-3"
                            color="light"
                            onClick={() =>
                              window.open(
                                'https://github.com/AnythingChat/AnythingChat/tree/main/py',
                                '_blank'
                              )
                            }
                          >
                            <div className="flex items-center">
                              <Image
                                src="/images/github-mark.svg"
                                alt="GitHub Logo"
                                width={20}
                                height={20}
                                className="mr-2"
                              />
                              <span>查看源码</span>
                            </div>
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                  {brandingConfig.homePage.githubCard && (
                    <Card className="w-full sm:w-1/2 flex flex-col modern-card animate-fade-in">
                      <CardHeader className="flex flex-row items-center space-x-2">
                        <Image
                          src="/images/javascript-logo.svg"
                          alt="JavaScript Logo"
                          width={30}
                          height={30}
                        />
                        <CardTitle>JavaScript SDK</CardTitle>
                      </CardHeader>
                      <CardContent className="flex flex-col justify-end flex-grow">
                        <div className="flex flex-row space-x-2">
                          <Button
                            className="rounded-md py-1 px-3"
                            color="light"
                            onClick={() =>
                              window.open(
                                'https://r2r-docs.sciphi.ai/documentation/js-sdk/introduction',
                                '_blank'
                              )
                            }
                          >
                            <div className="flex items-center">
                              <BookOpenText size={20} className="mr-2" />
                              <span>文档</span>
                            </div>
                          </Button>
                          <Button
                            className="rounded-md py-1 px-3"
                            color="light"
                            onClick={() =>
                              window.open(
                                'https://github.com/AnythingChat/AnythingChat/tree/main/js/sdk',
                                '_blank'
                              )
                            }
                          >
                            <div className="flex items-center">
                              <Image
                                src="/images/github-mark.svg"
                                alt="GitHub Logo"
                                width={20}
                                height={20}
                                className="mr-2"
                              />
                              <span>查看源码</span>
                            </div>
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
                <div className="flex flex-col sm:flex-row gap-4">
                  {brandingConfig.homePage.hatchetCard && (
                    <Card className="w-full sm:w-1/2 flex flex-col modern-card animate-fade-in">
                      <CardHeader className="flex flex-row items-center space-x-2">
                        <Image
                          src="/images/hatchet-logo.svg"
                          alt="Python Logo"
                          width={30}
                          height={30}
                        />
                        <CardTitle>Hatchet</CardTitle>
                      </CardHeader>
                      <CardContent className="flex flex-col justify-end flex-grow">
                        <div className="flex flex-row space-x-2">
                          <Button
                            className="rounded-md py-1 px-3"
                            color="light"
                            disabled={
                              !window.__RUNTIME_CONFIG__
                                ?.NEXT_PUBLIC_HATCHET_DASHBOARD_URL ||
                              window.__RUNTIME_CONFIG__.NEXT_PUBLIC_HATCHET_DASHBOARD_URL.includes(
                                '__NEXT_PUBLIC_HATCHET_DASHBOARD_URL__'
                              )
                            }
                            onClick={() => {
                              const url =
                                window.__RUNTIME_CONFIG__
                                  ?.NEXT_PUBLIC_HATCHET_DASHBOARD_URL;
                              if (
                                url &&
                                !url.includes(
                                  '__NEXT_PUBLIC_HATCHET_DASHBOARD_URL__'
                                )
                              ) {
                                window.open(url, '_blank');
                              }
                            }}
                            tooltip={
                              !window.__RUNTIME_CONFIG__
                                ?.NEXT_PUBLIC_HATCHET_DASHBOARD_URL ||
                              window.__RUNTIME_CONFIG__.NEXT_PUBLIC_HATCHET_DASHBOARD_URL.includes(
                                '__NEXT_PUBLIC_HATCHET_DASHBOARD_URL__'
                              ) ? (
                                <div>
                                  Hatchet Dashboard Deployment URL unavailable.
                                  <br />
                                  <a
                                    href="https://r2r-docs.sciphi.ai/cookbooks/orchestration"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-500 hover:text-blue-600 underline"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    Learn more about orchestration with{' '}
                                    {brandingConfig.deploymentName}
                                    Full.
                                  </a>
                                </div>
                              ) : undefined
                            }
                          >
                            <div className="flex items-center">
                              <PanelsTopLeft size={20} className="mr-2" />
                              <span>控制台</span>
                            </div>
                          </Button>
                          <Button
                            className="rounded-md py-1 px-3"
                            color="light"
                            onClick={() =>
                              window.open(
                                'https://github.com/hatchet-dev/hatchet',
                                '_blank'
                              )
                            }
                          >
                            <div className="flex items-center">
                              <Image
                                src="/images/github-mark.svg"
                                alt="GitHub Logo"
                                width={20}
                                height={20}
                                className="mr-2"
                              />
                              <span>查看源码</span>
                            </div>
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                  <div className="w-full sm:w-1/2"></div>
                </div>
              </div>
            </div>

            {/* Right column - Cards */}
            <div className="w-full lg:w-1/3 flex flex-col gap-4">
              {/* R2R Server Cards */}
              <div className="flex flex-col gap-4 flex-grow">
                {pipeline && (
                  <R2RServerCard
                    pipeline={pipeline}
                    onStatusChange={setIsConnected}
                  />
                )}

                <div className="flex-grow">
                  <RequestsCard />
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </Layout>
  );
};

export default HomePage;
