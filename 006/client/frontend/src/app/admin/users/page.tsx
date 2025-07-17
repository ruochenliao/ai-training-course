'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlusCircle, UserCog } from 'lucide-react';

export default function UserManagementPage() {

    // Placeholder for future data fetching and state management
    const users = [
        { id: 1, name: 'Alice Wonderland', email: 'alice@example.com', role: '管理员', status: '活跃' },
        { id: 2, name: 'Bob The Builder', email: 'bob@example.com', role: '编辑', status: '活跃' },
        { id: 3, name: 'Charlie Chaplin', email: 'charlie@example.com', role: '访客', status: '禁用' },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold text-cyan-400 tracking-tight">用户管理</h1>
                <Button className="bg-cyan-600 hover:bg-cyan-700 text-white">
                    <PlusCircle className="mr-2 h-4 w-4" /> 添加用户
                </Button>
            </div>

            <Card className="bg-gray-800 border-gray-700 text-gray-100">
                <CardHeader>
                    <CardTitle className="text-xl text-gray-200">用户列表</CardTitle>
                    <CardDescription className="text-gray-400">管理您的系统用户和权限。</CardDescription>
                </CardHeader>
                <CardContent>
                     {/* Placeholder for a data table or user list component */}
                     <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-700">
                            <thead className="bg-gray-750">
                                <tr>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">姓名</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">邮箱</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">角色</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">状态</th>
                                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">操作</th>
                                </tr>
                            </thead>
                            <tbody className="bg-gray-800 divide-y divide-gray-700">
                                {users.map((user) => (
                                    <tr key={user.id} className="hover:bg-gray-750 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{user.name}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{user.email}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{user.role}</td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${user.status === '活跃' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                                                {user.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <Button variant="ghost" size="sm" className="text-cyan-400 hover:text-cyan-300">
                                                <UserCog className="h-4 w-4 mr-1" /> 编辑
                                            </Button>
                                            {/* Add delete/other actions here */}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {/* Add pagination here */}
                </CardContent>
            </Card>
        </div>
    );
} 