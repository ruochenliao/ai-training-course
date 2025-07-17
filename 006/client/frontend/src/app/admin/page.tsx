'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Users, Database } from 'lucide-react';

// Example Stat Card Component
interface StatCardProps {
    title: string;
    value: string | number;
    icon: React.ElementType;
    description: string;
    colorClass: string; // e.g., 'text-cyan-400'
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, description, colorClass }) => {
    return (
        <Card className="bg-gray-800 border-gray-700 hover:border-cyan-600 transition-colors duration-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-300">{title}</CardTitle>
                <Icon className={`h-5 w-5 ${colorClass}`} />
            </CardHeader>
            <CardContent>
                <div className={`text-2xl font-bold ${colorClass}`}>{value}</div>
                <p className="text-xs text-gray-400 mt-1">{description}</p>
            </CardContent>
        </Card>
    );
};


export default function AdminDashboardPage() {
    const router = useRouter();
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

    useEffect(() => {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            console.log('No access token found, redirecting to login.');
            router.push('/admin/login');
        } else {
            setIsAuthenticated(true);
        }
    }, [router]);

    if (isAuthenticated === null) {
        return (
            <div className="flex justify-center items-center min-h-screen">
                <p className="text-white text-lg">正在检查登录状态...</p>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <h1 className="text-3xl font-bold text-cyan-400 tracking-tight mb-6">管理后台概览</h1>

            {/* Statistics Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                 <StatCard
                    title="活跃用户"
                    value="1,234"
                    icon={Users}
                    description="+20.1% from last month"
                    colorClass="text-cyan-400"
                />
                <StatCard
                    title="知识库条目"
                    value="573"
                    icon={Database}
                    description="+180 since last week"
                    colorClass="text-emerald-400"
                />
                 <StatCard
                    title="系统活动"
                    value="High"
                    icon={Activity}
                    description="Last check: 5 mins ago"
                    colorClass="text-amber-400"
                />
            </div>

            {/* Placeholder for other dashboard elements */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="bg-gray-800 border-gray-700">
                    <CardHeader>
                        <CardTitle className="text-xl text-gray-200">近期活动</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-gray-400">这里可以显示最近的用户登录、内容更新等...</p>
                        {/* Add activity feed component here */}
                    </CardContent>
                </Card>
                <Card className="bg-gray-800 border-gray-700">
                    <CardHeader>
                        <CardTitle className="text-xl text-gray-200">系统状态</CardTitle>
                    </CardHeader>
                    <CardContent>
                         <p className="text-gray-400">显示 CPU、内存使用情况等...</p>
                        {/* Add system status component here */}
                    </CardContent>
                </Card>
            </div>

            {/* Add more components as needed */}

        </div>
    );
} 