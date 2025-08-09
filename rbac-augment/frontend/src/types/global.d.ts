// Copyright (c) 2025 左岚. All rights reserved.

/**
 * 全局类型声明文件
 */

// 全局JSX命名空间声明
declare global {
  namespace JSX {
    interface Element {}
    interface ElementClass {}
    interface ElementAttributesProperty {}
    interface ElementChildrenAttribute {}
    interface IntrinsicElements {}
  }
}

// 确保此文件被视为模块
export {}