'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Upload, FileText, BrainCircuit, Search, Trash2 } from 'lucide-react';

export default function KnowledgeBasePage() {

    // Placeholder for knowledge base items
    const knowledgeItems = [
        { id: 'doc1', name: 'Onboarding Guide.pdf', type: 'PDF', size: '2.5MB', status: '已索引' },
        { id: 'web1', name: 'https://example.com/faq', type: '网页', size: 'N/A', status: '索引中' },
        { id: 'txt1', name: 'Company Policies.txt', type: 'TXT', size: '15KB', status: '错误' },
    ];

    return (
        <div className="space-y-6">
            {/* Header and Actions */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <h1 className="text-3xl font-bold text-cyan-400 tracking-tight">知识库管理</h1>
                <div className="flex gap-2 flex-wrap">
                    <Button className="bg-cyan-600 hover:bg-cyan-700 text-white">
                        <Upload className="mr-2 h-4 w-4" /> 上传文件
                    </Button>
                    <Button variant="outline" className="border-cyan-600 text-cyan-400 hover:bg-cyan-900/50 hover:text-cyan-300">
                        <FileText className="mr-2 h-4 w-4" /> 添加文本
                    </Button>
                     <Button variant="outline" className="border-cyan-600 text-cyan-400 hover:bg-cyan-900/50 hover:text-cyan-300">
                        <BrainCircuit className="mr-2 h-4 w-4" /> 添加网址
                    </Button>
                </div>
            </div>

            {/* Search and Filters (Placeholder) */}
            <div className="flex gap-2">
                 <Input 
                    type="search" 
                    placeholder="搜索知识库内容..."
                    className="max-w-sm bg-gray-700 border-gray-600 text-white focus:border-cyan-500 focus:ring-cyan-500"
                 />
                 {/* Add filter dropdowns here if needed */}
            </div>

            {/* Knowledge Base Items List */}
            <Card className="bg-gray-800 border-gray-700 text-gray-100">
                <CardHeader>
                    <CardTitle className="text-xl text-gray-200">知识源</CardTitle>
                    <CardDescription className="text-gray-400">管理用于 AI 回答的知识来源。</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-700">
                            <thead className="bg-gray-750">
                                <tr>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">名称/来源</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">类型</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">大小</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">状态</th>
                                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">操作</th>
                                </tr>
                            </thead>
                            <tbody className="bg-gray-800 divide-y divide-gray-700">
                                {knowledgeItems.map((item) => (
                                    <tr key={item.id} className="hover:bg-gray-750 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white truncate max-w-xs" title={item.name}>{item.name}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{item.type}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{item.size}</td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                                ${item.status === '已索引' ? 'bg-green-900 text-green-300' : item.status === '索引中' ? 'bg-yellow-900 text-yellow-300' : 'bg-red-900 text-red-300'}`}>
                                                {item.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                                            <Button variant="ghost" size="icon" className="text-cyan-400 hover:text-cyan-300">
                                                <Search className="h-4 w-4" />
                                                <span className="sr-only">查看</span>
                                            </Button>
                                             <Button variant="ghost" size="icon" className="text-red-500 hover:text-red-400">
                                                <Trash2 className="h-4 w-4" />
                                                <span className="sr-only">删除</span>
                                            </Button>
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