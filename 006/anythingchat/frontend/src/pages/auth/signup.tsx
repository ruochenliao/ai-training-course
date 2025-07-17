import { Eye, EyeOff } from 'lucide-react';
import { useRouter } from 'next/router';
import React, { useState, useEffect } from 'react';

import Layout from '@/components/Layout';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/input';
import { useUserContext } from '@/context/UserContext';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmedPassword, setConfirmedPassword] = useState('');
  const [deploymentUrl, setDeploymentUrl] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [passwordsMatch, setPasswordsMatch] = useState(true);
  const { login, register } = useUserContext();
  const router = useRouter();

  const handleLoginClick = () => {
    router.push('/');
  };

  useEffect(() => {
    const url = process.env.R2R_DEPLOYMENT_URL || 'http://localhost:7272';
    setDeploymentUrl(url);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!checkPasswordsMatch()) {
      setPasswordsMatch(false);
      return;
    }
    try {
      await register(email, password, deploymentUrl);
      await login(email, password, deploymentUrl);
      router.push('/');
    } catch (error) {
      console.error('Registration or login failed:', error);
      alert(
        'Registration or login failed. Ensure that your server is running at the specified URL or check your credentials and try again.'
      );
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const checkPasswordsMatch = () => {
    return password === confirmedPassword;
  };

  const handlePasswordBlur = () => {
    setPasswordsMatch(checkPasswordsMatch());
  };

  return (
    <Layout includeFooter={false}>
      <div className="flex flex-col justify-center items-center min-h-screen bg-white dark:bg-zinc-900">
        <form
          onSubmit={handleSubmit}
          className="bg-zinc-100 dark:bg-zinc-800 shadow-md rounded px-8 pt-6 pb-8 mb-4 w-full max-w-md"
        >
          <div className="mb-4">
            <label
              className="block text-gray-700 dark:text-gray-200 text-sm font-bold mb-2"
              htmlFor="email"
            >
              邮箱
            </label>
            <Input
              id="email"
              type="email"
              placeholder="邮箱"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </div>
          <div className="mb-6">
            <div className="flex items-center justify-between">
              <label
                className="block text-gray-700 dark:text-gray-200 text-sm font-bold mb-2 flex-grow"
                htmlFor="password"
              >
                密码
              </label>
              {!passwordsMatch && (
                <span className="text-red-400 text-sm font-bold mb-2">
                  密码不匹配
                </span>
              )}
            </div>
            <div className="relative">
              <Input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onBlur={handlePasswordBlur}
                className={`pr-10 ${passwordsMatch ? '' : 'border-red-400'}`}
                autoComplete="current-password"
              />

              <button
                type="button"
                onClick={togglePasswordVisibility}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" aria-hidden="true" />
                ) : (
                  <Eye className="h-5 w-5" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>
          <div className="mb-6">
            <label
              className="block text-gray-700 dark:text-gray-200 text-sm font-bold mb-2"
              htmlFor="confirm-password"
            >
              确认密码
            </label>
            <div className="relative">
              <Input
                id="confirm-password"
                name="confirm-password"
                type={showPassword ? 'text' : 'password'}
                placeholder="确认密码"
                value={confirmedPassword}
                onChange={(e) => setConfirmedPassword(e.target.value)}
                onBlur={handlePasswordBlur}
                className={`pr-10 ${passwordsMatch ? '' : 'border-red-400'}`}
              />
              <button
                type="button"
                onClick={togglePasswordVisibility}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" aria-hidden="true" />
                ) : (
                  <Eye className="h-5 w-5" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <Button color="primary" className="w-full">
              邮箱注册
            </Button>
          </div>
        </form>

        <div className="text-gray-700 dark:text-gray-400 text-sm font-bold mb-2">
          <p>
            已有账户？{' '}
            <span
              onClick={handleLoginClick}
              className="text-accent-base cursor-pointer hover:underline"
            >
              登录
            </span>
            。
          </p>
        </div>
      </div>
    </Layout>
  );
};

export default LoginPage;
