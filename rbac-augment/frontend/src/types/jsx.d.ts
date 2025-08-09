// Copyright (c) 2025 左岚. All rights reserved.

/**
 * JSX 命名空间类型声明
 * 用于解决 Element Plus 组件库中的 JSX 类型错误
 */

// 声明 JSX 命名空间
namespace JSX {
  interface Element {}
  interface ElementClass {}
  interface ElementAttributesProperty {}
  interface ElementChildrenAttribute {}
  interface IntrinsicElements {}
}

// 确保此文件被视为模块
export {}
export {}