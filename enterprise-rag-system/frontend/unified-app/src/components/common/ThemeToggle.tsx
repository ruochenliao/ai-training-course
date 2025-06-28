'use client';

import { Button } from 'antd';
import { SunOutlined, MoonOutlined } from '@ant-design/icons';
import { motion } from 'framer-motion';
import { useTheme } from '@/contexts/ThemeContext';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      <Button
        type="text"
        shape="circle"
        size="large"
        onClick={toggleTheme}
        className="flex items-center justify-center bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 hover:bg-white dark:hover:bg-gray-700 shadow-lg"
        icon={
          <motion.div
            initial={false}
            animate={{ rotate: theme === 'dark' ? 180 : 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
          >
            {theme === 'light' ? (
              <MoonOutlined className="text-gray-600 dark:text-gray-300" />
            ) : (
              <SunOutlined className="text-yellow-500" />
            )}
          </motion.div>
        }
      />
    </motion.div>
  );
}
