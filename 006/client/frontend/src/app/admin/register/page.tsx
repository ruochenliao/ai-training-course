'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { UserPlus } from 'lucide-react'

// --- Helper function to get base URL ---
const getApiBaseUrl = () => {
  return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
};

export default function Register() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleRegister = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsLoading(true)
    setError('')
    setSuccess('')

    if (password !== confirmPassword) {
      setError('密码和确认密码不匹配。')
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/users/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          email: email,
          password: password,
          is_admin: true // Assuming admin registration sets is_admin to true
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Registration successful:', data);
        setSuccess('注册成功！正在跳转到登录页面...');
        setTimeout(() => {
          router.push('/admin/login'); // Redirect to login page after successful registration
        }, 2000);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || '注册失败，请检查您输入的信息。');
      }
    } catch (err) {
      console.error("Registration error:", err);
      setError('发生网络错误，请稍后重试。');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black p-4">
      <Card className="w-full max-w-md bg-gray-800 border-gray-700 shadow-2xl shadow-purple-500/20 text-gray-100">
        <CardHeader className="space-y-1 text-center">
          <UserPlus className="mx-auto h-10 w-10 text-purple-400 mb-4" />
          <CardTitle className="text-2xl font-bold text-purple-400">管理员注册</CardTitle>
          <CardDescription className="text-gray-400">创建一个新的管理员账户</CardDescription>
        </CardHeader>
        <form onSubmit={handleRegister}>
          <CardContent className="space-y-4"> {/* Reduced space-y */} 
            <div className="space-y-2">
              <Label htmlFor="username" className="text-gray-300">用户名</Label>
              <Input
                id="username"
                type="text"
                placeholder="输入用户名"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="bg-gray-700 border-gray-600 text-white focus:border-purple-500 focus:ring-purple-500"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-300">邮箱</Label>
              <Input
                id="email"
                type="email"
                placeholder="输入邮箱地址"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-gray-700 border-gray-600 text-white focus:border-purple-500 focus:ring-purple-500"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-300">密码</Label>
              <Input
                id="password"
                type="password"
                placeholder="输入密码"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-gray-700 border-gray-600 text-white focus:border-purple-500 focus:ring-purple-500"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-gray-300">确认密码</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="再次输入密码"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="bg-gray-700 border-gray-600 text-white focus:border-purple-500 focus:ring-purple-500"
                disabled={isLoading}
              />
            </div>
            {error && (
              <p className="text-sm text-red-500 text-center">{error}</p>
            )}
            {success && (
              <p className="text-sm text-green-500 text-center">{success}</p>
            )}
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold" disabled={isLoading}>
              {isLoading ? '注册中...' : '注册'}
            </Button>
            <Link href="/admin/login" className="text-sm text-purple-400 hover:text-purple-300 text-center w-full">
              已有账户？点击登录
            </Link>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
} 