import {useCallback, useEffect, useState} from 'react';

/**
 * 本地存储Hook
 * @param key 存储键
 * @param initialValue 初始值
 */
function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((val: T) => T)) => void, () => void] {
  // 获取初始值
  const readValue = useCallback((): T => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  }, [initialValue, key]);

  // 状态保存值
  const [storedValue, setStoredValue] = useState<T>(readValue);

  // 返回一个包装版本的useState的setter函数
  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      if (typeof window === 'undefined') {
        console.warn(`Tried setting localStorage key "${key}" even though environment is not a client`);
        return;
      }

      try {
        // 允许值是一个函数，类似于useState
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        
        // 保存到state
        setStoredValue(valueToStore);
        
        // 保存到localStorage
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
        
        // 触发自定义事件，以便其他组件可以响应存储的变化
        window.dispatchEvent(new Event('local-storage'));
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  // 移除项目
  const removeValue = useCallback(() => {
    if (typeof window === 'undefined') {
      console.warn(`Tried removing localStorage key "${key}" even though environment is not a client`);
      return;
    }

    try {
      // 从localStorage中移除
      window.localStorage.removeItem(key);
      
      // 重置状态为初始值
      setStoredValue(initialValue);
      
      // 触发自定义事件
      window.dispatchEvent(new Event('local-storage'));
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [initialValue, key]);

  // 监听存储事件，以便在其他窗口/标签页中更新
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key) {
        setStoredValue(e.newValue ? JSON.parse(e.newValue) : initialValue);
      }
    };

    // 监听本地存储变化
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('local-storage', () => setStoredValue(readValue()));

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('local-storage', () => setStoredValue(readValue()));
    };
  }, [key, readValue, initialValue]);

  return [storedValue, setValue, removeValue];
}

export default useLocalStorage; 