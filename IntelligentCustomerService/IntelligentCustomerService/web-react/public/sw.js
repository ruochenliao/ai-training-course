// Service Worker for PWA functionality
// 提供离线缓存、推送通知等PWA功能

const CACHE_NAME = 'intelligent-customer-service-v1.0.0';
const STATIC_CACHE_NAME = 'static-cache-v1.0.0';
const DYNAMIC_CACHE_NAME = 'dynamic-cache-v1.0.0';

// 需要缓存的静态资源
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/favicon.ico',
  // 添加其他静态资源
];

// 需要缓存的API端点
const CACHE_API_PATTERNS = [
  /^\/api\/v1\/knowledge-graph\/statistics/,
  /^\/api\/v1\/monitoring\/health/,
  /^\/api\/v1\/chat\/conversations/,
];

// 不需要缓存的API端点
const NO_CACHE_API_PATTERNS = [
  /^\/api\/v1\/chat\/stream/,
  /^\/api\/v1\/monitoring\/metrics/,
  /^\/api\/v1\/auth/,
];

// Service Worker 安装事件
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Static assets cached');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Failed to cache static assets', error);
      })
  );
});

// Service Worker 激活事件
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            // 删除旧版本的缓存
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName !== CACHE_NAME) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

// 网络请求拦截
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // 只处理同源请求
  if (url.origin !== location.origin) {
    return;
  }
  
  // 处理不同类型的请求
  if (request.method === 'GET') {
    if (url.pathname.startsWith('/api/')) {
      // API请求处理
      event.respondWith(handleApiRequest(request));
    } else {
      // 静态资源请求处理
      event.respondWith(handleStaticRequest(request));
    }
  }
});

// 处理静态资源请求
async function handleStaticRequest(request) {
  try {
    // 先尝试从缓存获取
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('Service Worker: Serving from cache', request.url);
      return cachedResponse;
    }
    
    // 缓存未命中，从网络获取
    const networkResponse = await fetch(request);
    
    // 缓存成功的响应
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
      console.log('Service Worker: Cached new resource', request.url);
    }
    
    return networkResponse;
    
  } catch (error) {
    console.error('Service Worker: Failed to fetch static resource', error);
    
    // 网络失败时，尝试返回离线页面
    if (request.destination === 'document') {
      const offlineResponse = await caches.match('/offline.html');
      if (offlineResponse) {
        return offlineResponse;
      }
    }
    
    // 返回基本的离线响应
    return new Response('离线模式：资源不可用', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'text/plain; charset=utf-8' }
    });
  }
}

// 处理API请求
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  // 检查是否应该跳过缓存
  const shouldSkipCache = NO_CACHE_API_PATTERNS.some(pattern => 
    pattern.test(url.pathname)
  );
  
  if (shouldSkipCache) {
    // 直接从网络获取，不缓存
    try {
      return await fetch(request);
    } catch (error) {
      console.error('Service Worker: API request failed', error);
      return new Response(JSON.stringify({
        error: '网络连接失败',
        offline: true
      }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
  
  // 检查是否应该缓存
  const shouldCache = CACHE_API_PATTERNS.some(pattern => 
    pattern.test(url.pathname)
  );
  
  if (shouldCache) {
    return handleCacheableApiRequest(request);
  }
  
  // 默认网络优先策略
  try {
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    console.error('Service Worker: API request failed', error);
    return new Response(JSON.stringify({
      error: '网络连接失败',
      offline: true
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// 处理可缓存的API请求
async function handleCacheableApiRequest(request) {
  try {
    // 网络优先策略
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // 缓存成功的响应
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
      console.log('Service Worker: Cached API response', request.url);
    }
    
    return networkResponse;
    
  } catch (error) {
    console.error('Service Worker: Network request failed, trying cache', error);
    
    // 网络失败时从缓存获取
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('Service Worker: Serving API from cache', request.url);
      
      // 添加离线标识
      const responseData = await cachedResponse.json();
      responseData._offline = true;
      responseData._cached_at = new Date().toISOString();
      
      return new Response(JSON.stringify(responseData), {
        status: cachedResponse.status,
        statusText: cachedResponse.statusText,
        headers: cachedResponse.headers
      });
    }
    
    // 缓存也没有，返回离线响应
    return new Response(JSON.stringify({
      error: '数据不可用',
      offline: true,
      message: '请检查网络连接'
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// 推送通知事件
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push notification received');
  
  const options = {
    body: '您有新的消息',
    icon: '/icon-192x192.png',
    badge: '/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: '查看详情',
        icon: '/icon-explore.png'
      },
      {
        action: 'close',
        title: '关闭',
        icon: '/icon-close.png'
      }
    ]
  };
  
  if (event.data) {
    try {
      const payload = event.data.json();
      options.body = payload.body || options.body;
      options.title = payload.title || '智能客服系统';
      options.data = { ...options.data, ...payload.data };
    } catch (error) {
      console.error('Service Worker: Failed to parse push payload', error);
    }
  }
  
  event.waitUntil(
    self.registration.showNotification('智能客服系统', options)
  );
});

// 通知点击事件
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    // 打开应用
    event.waitUntil(
      clients.openWindow('/')
    );
  } else if (event.action === 'close') {
    // 关闭通知
    console.log('Service Worker: Notification closed');
  } else {
    // 默认行为：打开应用
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// 后台同步事件
self.addEventListener('sync', (event) => {
  console.log('Service Worker: Background sync triggered');
  
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

// 执行后台同步
async function doBackgroundSync() {
  try {
    console.log('Service Worker: Performing background sync');
    
    // 这里可以执行后台数据同步任务
    // 例如：上传离线时的聊天记录、同步用户设置等
    
    // 示例：同步离线聊天记录
    const offlineMessages = await getOfflineMessages();
    if (offlineMessages.length > 0) {
      await syncOfflineMessages(offlineMessages);
    }
    
    console.log('Service Worker: Background sync completed');
    
  } catch (error) {
    console.error('Service Worker: Background sync failed', error);
  }
}

// 获取离线消息（示例）
async function getOfflineMessages() {
  // 从IndexedDB或其他存储获取离线消息
  return [];
}

// 同步离线消息（示例）
async function syncOfflineMessages(messages) {
  // 将离线消息发送到服务器
  for (const message of messages) {
    try {
      await fetch('/api/v1/chat/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(message)
      });
    } catch (error) {
      console.error('Service Worker: Failed to sync message', error);
    }
  }
}

// 错误处理
self.addEventListener('error', (event) => {
  console.error('Service Worker: Error occurred', event.error);
});

// 未处理的Promise拒绝
self.addEventListener('unhandledrejection', (event) => {
  console.error('Service Worker: Unhandled promise rejection', event.reason);
});

console.log('Service Worker: Script loaded');
