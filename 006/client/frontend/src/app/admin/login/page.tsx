'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { motion } from 'framer-motion'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { LogIn } from 'lucide-react'

// --- Helper function to get base URL ---
const getApiBaseUrl = () => {
  // Assuming backend runs on port 8000 in development
  return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
};

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsLoading(true)
    setError('')

    // --- Real Authentication Logic ---
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Login successful, token:', data.access_token);
        // Store the token in localStorage
        localStorage.setItem('accessToken', data.access_token);
        localStorage.setItem('tokenType', data.token_type);
        router.push('/admin'); // Redirect to admin dashboard
      } else {
        const errorData = await response.json();
        setError(errorData.detail || '登录失败，请检查您的凭据。');
      }
    } catch (err) {
        console.error("Login error:", err);
        setError('发生网络错误，请稍后重试。');
    } finally {
        setIsLoading(false);
    }
    // --- End Real Authentication ---
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black p-4">
      <Card className="w-full max-w-md bg-gray-800 border-gray-700 shadow-2xl shadow-cyan-500/20 text-gray-100">
        <CardHeader className="space-y-1 text-center">
          <LogIn className="mx-auto h-10 w-10 text-cyan-400 mb-4" />
          <CardTitle className="text-2xl font-bold text-cyan-400">管理员登录</CardTitle>
          <CardDescription className="text-gray-400">请输入您的凭据以访问管理后台</CardDescription>
        </CardHeader>
        <form onSubmit={handleLogin}>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-gray-300">用户名</Label>
              <Input
                id="username"
                type="text"
                placeholder="例如 admin"
                required
                value={username}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUsername(e.target.value)}
                className="bg-gray-700 border-gray-600 text-white focus:border-cyan-500 focus:ring-cyan-500"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-300">密码</Label>
              <Input
                id="password"
                type="password"
                placeholder="********"
                required
                value={password}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                className="bg-gray-700 border-gray-600 text-white focus:border-cyan-500 focus:ring-cyan-500"
                disabled={isLoading}
              />
            </div>
            {error && (
              <p className="text-sm text-red-500 text-center">{error}</p>
            )}
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full bg-cyan-600 hover:bg-cyan-700 text-white font-bold" disabled={isLoading}>
              {isLoading ? '登录中...' : '登录'}
            </Button>
            <Link href="/admin/register" className="text-sm text-cyan-400 hover:text-cyan-300 text-center w-full">
              还没有账户？点击注册
            </Link>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
} 