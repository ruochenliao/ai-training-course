'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Users, Database, Settings, Menu, X, Sun, Moon } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useTheme } from "next-themes"; // Assumes you have next-themes installed

// --- Sidebar Navigation Item Component ---
interface NavItemProps {
    href: string;
    icon: React.ElementType;
    label: string;
    isCollapsed: boolean;
}

const NavItem: React.FC<NavItemProps> = ({ href, icon: Icon, label, isCollapsed }) => {
    const pathname = usePathname();
    const isActive = pathname === href || (href !== '/admin' && pathname.startsWith(href));

    return (
        <TooltipProvider delayDuration={0}>
            <Tooltip>
                <TooltipTrigger asChild>
                    <Link href={href}>
                        <Button
                            variant={isActive ? "secondary" : "ghost"}
                            className={`w-full flex items-center justify-start px-3 py-2 rounded-md transition-colors duration-200 ease-in-out 
                                ${isCollapsed ? 'justify-center' : 'justify-start'} 
                                ${isActive ? 'bg-gray-700 text-cyan-400' : 'text-gray-400 hover:bg-gray-700 hover:text-white'}`}
                        >
                            <Icon className={`h-5 w-5 ${isCollapsed ? '' : 'mr-3'}`} />
                            {!isCollapsed && <span className="font-medium">{label}</span>}
                        </Button>
                    </Link>
                </TooltipTrigger>
                {isCollapsed && (
                    <TooltipContent side="right" className="bg-gray-900 text-white border-gray-700">
                        <p>{label}</p>
                    </TooltipContent>
                )}
            </Tooltip>
        </TooltipProvider>
    );
};

// --- Theme Toggle Component ---
const ThemeToggle: React.FC<{ isCollapsed: boolean }> = ({ isCollapsed }) => {
    const { theme, setTheme } = useTheme();

    const toggleTheme = () => {
        setTheme(theme === 'dark' ? 'light' : 'dark');
    };

    return (
        <TooltipProvider delayDuration={0}>
            <Tooltip>
                <TooltipTrigger asChild>
                    <Button
                        variant="ghost"
                        size={isCollapsed ? "icon" : "default"}
                        onClick={toggleTheme}
                        className={`w-full flex items-center px-3 py-2 rounded-md transition-colors duration-200 ease-in-out 
                                    ${isCollapsed ? 'justify-center' : 'justify-start'} 
                                    text-gray-400 hover:bg-gray-700 hover:text-white`}
                    >
                        {theme === 'dark' ? <Sun className={`h-5 w-5 ${isCollapsed ? '' : 'mr-3'}`} /> : <Moon className={`h-5 w-5 ${isCollapsed ? '' : 'mr-3'}`} />}
                        {!isCollapsed && <span className="font-medium">切换主题</span>}
                    </Button>
                </TooltipTrigger>
                {isCollapsed && (
                    <TooltipContent side="right" className="bg-gray-900 text-white border-gray-700">
                        <p>切换到 {theme === 'dark' ? '亮色' : '暗色'} 模式</p>
                    </TooltipContent>
                )}
            </Tooltip>
        </TooltipProvider>
    );
}

// --- Main Layout Component ---
export default function AdminLayout({ children }: { children: React.ReactNode }) {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const toggleSidebar = () => setIsCollapsed(!isCollapsed);
    const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);

    const navItems = [
        { href: '/admin', icon: Home, label: '概览' },
        { href: '/admin/users', icon: Users, label: '用户管理' },
        { href: '/admin/knowledge', icon: Database, label: '知识库管理' },
        { href: '/admin/settings', icon: Settings, label: '设置' },
    ];

    return (
        <div className="flex h-screen bg-gray-900 text-gray-100">
            {/* Desktop Sidebar */}
            <aside
                className={`hidden md:flex flex-col bg-gray-800 border-r border-gray-700 transition-all duration-300 ease-in-out ${isCollapsed ? 'w-20' : 'w-64'}`}
            >
                <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'} h-16 px-4 border-b border-gray-700`}>
                   {!isCollapsed && <span className="text-xl font-semibold text-cyan-400">管理后台</span>}
                    <Button variant="ghost" size="icon" onClick={toggleSidebar} className="text-gray-400 hover:text-white">
                        {isCollapsed ? <Menu className="h-6 w-6"/> : <X className="h-6 w-6"/>}
                    </Button>
                </div>
                <nav className="flex-1 px-2 py-4 space-y-2 overflow-y-auto">
                    {navItems.map((item) => (
                        <NavItem key={item.href} {...item} isCollapsed={isCollapsed} />
                    ))}
                </nav>
                 <div className="px-2 py-4 border-t border-gray-700">
                    <ThemeToggle isCollapsed={isCollapsed} />
                </div>
            </aside>

            {/* Mobile Menu Button */}
            <div className="md:hidden fixed top-4 left-4 z-20">
                <Button variant="secondary" size="icon" onClick={toggleMobileMenu} className="bg-gray-800 text-cyan-400 hover:bg-gray-700">
                    {isMobileMenuOpen ? <X className="h-6 w-6"/> : <Menu className="h-6 w-6"/>}
                </Button>
            </div>

             {/* Mobile Sidebar */}
             <aside
                className={`fixed inset-y-0 left-0 z-10 flex md:hidden flex-col bg-gray-800 border-r border-gray-700 w-64 transform transition-transform duration-300 ease-in-out 
                           ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}
            >
                <div className="flex items-center justify-between h-16 px-4 border-b border-gray-700">
                    <span className="text-xl font-semibold text-cyan-400">管理后台</span>
                     <Button variant="ghost" size="icon" onClick={toggleMobileMenu} className="text-gray-400 hover:text-white">
                        <X className="h-6 w-6"/>
                    </Button>
                </div>
                <nav className="flex-1 px-2 py-4 space-y-2 overflow-y-auto" onClick={() => setIsMobileMenuOpen(false)}>
                     {navItems.map((item) => (
                        <NavItem key={item.href} {...item} isCollapsed={false} /> // Mobile always expanded view
                    ))}
                </nav>
                 <div className="px-2 py-4 border-t border-gray-700">
                    <ThemeToggle isCollapsed={false} />
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col overflow-hidden">
                {/* Optional Header */}
                {/* <header className="bg-gray-800 border-b border-gray-700 h-16 flex items-center px-6">
                    <h1 className="text-xl font-semibold">Dashboard</h1>
                </header> */}
                <div className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-900 p-6">
                    {/* Page content goes here */}
                    {children}
                </div>
            </main>
        </div>
    );
} 