import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

// 扩展dayjs插件
dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

/**
 * 格式化时间
 * @param time 时间
 * @param format 格式
 * @returns 格式化后的时间字符串
 */
export function formatTime(time: string | Date | number, format = 'YYYY-MM-DD HH:mm:ss'): string {
  return dayjs(time).format(format);
}

/**
 * 格式化相对时间
 * @param time 时间
 * @returns 相对时间字符串
 */
export function formatRelativeTime(time: string | Date | number): string {
  return dayjs(time).fromNow();
}

/**
 * 格式化日期
 * @param time 时间
 * @param format 格式
 * @returns 格式化后的日期字符串
 */
export function formatDate(time: string | Date | number, format = 'YYYY-MM-DD'): string {
  return dayjs(time).format(format);
}

/**
 * 格式化时间戳
 * @param timestamp 时间戳（毫秒）
 * @param format 格式
 * @returns 格式化后的时间字符串
 */
export function formatTimestamp(timestamp: number, format = 'YYYY-MM-DD HH:mm:ss'): string {
  return dayjs(timestamp).format(format);
}

/**
 * 获取当前时间戳
 * @returns 当前时间戳（毫秒）
 */
export function getCurrentTimestamp(): number {
  return Date.now();
}

/**
 * 获取今天开始时间戳
 * @returns 今天开始时间戳（毫秒）
 */
export function getStartOfDayTimestamp(): number {
  return dayjs().startOf('day').valueOf();
}

/**
 * 获取今天结束时间戳
 * @returns 今天结束时间戳（毫秒）
 */
export function getEndOfDayTimestamp(): number {
  return dayjs().endOf('day').valueOf();
}

/**
 * 格式化持续时间
 * @param duration 持续时间（秒）
 * @returns 格式化后的持续时间字符串
 */
export function formatDuration(duration: number): string {
  if (duration < 60) {
    return `${Math.round(duration)}秒`;
  } else if (duration < 3600) {
    const minutes = Math.floor(duration / 60);
    const seconds = Math.round(duration % 60);
    return `${minutes}分${seconds}秒`;
  } else {
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    return `${hours}小时${minutes}分钟`;
  }
}

/**
 * 判断是否为今天
 * @param time 时间
 * @returns 是否为今天
 */
export function isToday(time: string | Date | number): boolean {
  return dayjs(time).isSame(dayjs(), 'day');
}

/**
 * 判断是否为昨天
 * @param time 时间
 * @returns 是否为昨天
 */
export function isYesterday(time: string | Date | number): boolean {
  return dayjs(time).isSame(dayjs().subtract(1, 'day'), 'day');
}

/**
 * 获取时间差
 * @param startTime 开始时间
 * @param endTime 结束时间
 * @param unit 单位
 * @returns 时间差
 */
export function getTimeDiff(
  startTime: string | Date | number,
  endTime: string | Date | number,
  unit: 'millisecond' | 'second' | 'minute' | 'hour' | 'day' = 'second'
): number {
  return dayjs(endTime).diff(dayjs(startTime), unit);
}

/**
 * 格式化聊天时间
 * @param time 时间
 * @returns 格式化后的聊天时间字符串
 */
export function formatChatTime(time: string | Date | number): string {
  const now = dayjs();
  const messageTime = dayjs(time);
  
  if (messageTime.isSame(now, 'day')) {
    // 今天：显示时间
    return messageTime.format('HH:mm');
  } else if (messageTime.isSame(now.subtract(1, 'day'), 'day')) {
    // 昨天：显示"昨天 时间"
    return `昨天 ${messageTime.format('HH:mm')}`;
  } else if (messageTime.isSame(now, 'year')) {
    // 今年：显示月日时间
    return messageTime.format('MM-DD HH:mm');
  } else {
    // 其他年份：显示完整日期时间
    return messageTime.format('YYYY-MM-DD HH:mm');
  }
}

/**
 * 格式化会话时间
 * @param time 时间
 * @returns 格式化后的会话时间字符串
 */
export function formatSessionTime(time: string | Date | number): string {
  const now = dayjs();
  const sessionTime = dayjs(time);
  
  if (sessionTime.isSame(now, 'day')) {
    // 今天：显示时间
    return sessionTime.format('HH:mm');
  } else if (sessionTime.isSame(now.subtract(1, 'day'), 'day')) {
    // 昨天：显示"昨天"
    return '昨天';
  } else if (sessionTime.isSame(now, 'year')) {
    // 今年：显示月日
    return sessionTime.format('MM-DD');
  } else {
    // 其他年份：显示年月日
    return sessionTime.format('YYYY-MM-DD');
  }
}

/**
 * 获取相对时间（多久前）
 * @param time 时间
 * @returns 相对时间字符串
 */
export function getTimeAgo(time: string | Date | number): string {
  return dayjs(time).fromNow();
}

export default {
  formatTime,
  formatRelativeTime,
  formatDate,
  formatTimestamp,
  getCurrentTimestamp,
  getStartOfDayTimestamp,
  getEndOfDayTimestamp,
  formatDuration,
  isToday,
  isYesterday,
  getTimeDiff,
  formatChatTime,
  formatSessionTime,
  getTimeAgo,
};