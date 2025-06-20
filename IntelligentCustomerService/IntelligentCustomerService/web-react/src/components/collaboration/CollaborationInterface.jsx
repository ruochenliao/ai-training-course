import React, { useState, useRef, useEffect } from 'react';
import { 
  Users, 
  MessageCircle, 
  Send, 
  UserPlus, 
  Settings,
  Mic,
  MicOff,
  Video,
  VideoOff,
  Phone,
  PhoneOff,
  MoreVertical,
  Crown,
  Circle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Badge } from '../ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { useToast } from '../ui/use-toast';

const CollaborationInterface = ({ currentUser, onRoomChange }) => {
  const [rooms, setRooms] = useState([]);
  const [currentRoom, setCurrentRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState([]);
  const [showCreateRoom, setShowCreateRoom] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const [newRoomDescription, setNewRoomDescription] = useState('');
  const [isPrivateRoom, setIsPrivateRoom] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(false);
  const [isInCall, setIsInCall] = useState(false);

  const websocketRef = useRef(null);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  const { toast } = useToast();

  // 初始化
  useEffect(() => {
    loadRooms();
    return () => {
      disconnectFromRoom();
    };
  }, []);

  // 自动滚动到最新消息
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadRooms = async () => {
    try {
      const response = await fetch(`/api/v1/collaboration/rooms?user_id=${currentUser?.id}`);
      const data = await response.json();
      
      if (data.success) {
        setRooms(data.rooms);
      }
    } catch (error) {
      console.error('加载房间列表失败:', error);
      toast({
        title: "加载失败",
        description: "无法加载房间列表",
        variant: "destructive"
      });
    }
  };

  const createRoom = async () => {
    if (!newRoomName.trim()) {
      toast({
        title: "输入错误",
        description: "请输入房间名称",
        variant: "destructive"
      });
      return;
    }

    try {
      const response = await fetch('/api/v1/collaboration/rooms', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: newRoomName,
          description: newRoomDescription,
          is_private: isPrivateRoom,
          created_by: currentUser?.id
        })
      });

      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "创建成功",
          description: "房间创建成功",
          variant: "success"
        });
        
        setShowCreateRoom(false);
        setNewRoomName('');
        setNewRoomDescription('');
        setIsPrivateRoom(false);
        
        loadRooms();
      } else {
        throw new Error(data.error || '创建房间失败');
      }
    } catch (error) {
      console.error('创建房间失败:', error);
      toast({
        title: "创建失败",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const joinRoom = async (roomId) => {
    try {
      // 先断开当前连接
      disconnectFromRoom();

      // 建立WebSocket连接
      const wsUrl = `ws://localhost:8000/api/v1/collaboration/rooms/${roomId}/ws?user_id=${currentUser?.id}&username=${currentUser?.username}&avatar=${currentUser?.avatar || ''}`;
      websocketRef.current = new WebSocket(wsUrl);

      websocketRef.current.onopen = () => {
        setIsConnected(true);
        toast({
          title: "连接成功",
          description: "已加入协作房间",
          variant: "success"
        });
      };

      websocketRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      };

      websocketRef.current.onclose = () => {
        setIsConnected(false);
        setCurrentRoom(null);
        setMessages([]);
        setUsers([]);
      };

      websocketRef.current.onerror = (error) => {
        console.error('WebSocket错误:', error);
        setIsConnected(false);
        toast({
          title: "连接错误",
          description: "无法连接到协作房间",
          variant: "destructive"
        });
      };

      // 设置当前房间
      const room = rooms.find(r => r.room_id === roomId);
      setCurrentRoom(room);
      
      if (onRoomChange) {
        onRoomChange(room);
      }
    } catch (error) {
      console.error('加入房间失败:', error);
      toast({
        title: "加入失败",
        description: "无法加入房间",
        variant: "destructive"
      });
    }
  };

  const disconnectFromRoom = () => {
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    setIsConnected(false);
    setCurrentRoom(null);
    setMessages([]);
    setUsers([]);
    setTypingUsers([]);
  };

  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'connected':
        // 连接成功
        break;
      case 'room_status':
        // 房间状态更新
        setUsers(message.content.users || []);
        setMessages(message.content.message_history || []);
        break;
      case 'chat':
        // 新聊天消息
        setMessages(prev => [...prev, message]);
        break;
      case 'user_join':
        // 用户加入
        setMessages(prev => [...prev, {
          ...message,
          content: { text: `${message.content.user.username} 加入了房间` },
          message_type: 'system'
        }]);
        break;
      case 'user_leave':
        // 用户离开
        setMessages(prev => [...prev, {
          ...message,
          content: { text: `${message.content.user.username} 离开了房间` },
          message_type: 'system'
        }]);
        break;
      case 'typing':
        // 用户正在输入
        setTypingUsers(prev => {
          if (!prev.includes(message.sender_id)) {
            return [...prev, message.sender_id];
          }
          return prev;
        });
        break;
      case 'stop_typing':
        // 用户停止输入
        setTypingUsers(prev => prev.filter(id => id !== message.sender_id));
        break;
      case 'voice_start':
        // 语音通话开始
        setIsInCall(true);
        break;
      case 'voice_end':
        // 语音通话结束
        setIsInCall(false);
        break;
      case 'error':
        toast({
          title: "协作错误",
          description: message.message,
          variant: "destructive"
        });
        break;
    }
  };

  const sendMessage = () => {
    if (!messageInput.trim() || !isConnected) return;

    const message = {
      type: 'chat',
      content: {
        text: messageInput,
        timestamp: new Date().toISOString()
      }
    };

    websocketRef.current.send(JSON.stringify(message));
    setMessageInput('');
    stopTyping();
  };

  const startTyping = () => {
    if (!isTyping && isConnected) {
      setIsTyping(true);
      websocketRef.current.send(JSON.stringify({
        type: 'typing',
        content: {}
      }));
    }

    // 重置停止输入计时器
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    typingTimeoutRef.current = setTimeout(() => {
      stopTyping();
    }, 3000);
  };

  const stopTyping = () => {
    if (isTyping && isConnected) {
      setIsTyping(false);
      websocketRef.current.send(JSON.stringify({
        type: 'stop_typing',
        content: {}
      }));
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }
  };

  const startVoiceCall = () => {
    if (!isConnected) return;

    websocketRef.current.send(JSON.stringify({
      type: 'voice_start',
      content: {}
    }));
    
    setIsInCall(true);
  };

  const endVoiceCall = () => {
    if (!isConnected) return;

    websocketRef.current.send(JSON.stringify({
      type: 'voice_end',
      content: {}
    }));
    
    setIsInCall(false);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getUserStatusColor = (status) => {
    switch (status) {
      case 'online': return 'bg-green-500';
      case 'away': return 'bg-yellow-500';
      case 'busy': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="flex h-full">
      {/* 房间列表 */}
      <div className="w-80 border-r bg-gray-50">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">协作房间</h3>
            <Dialog open={showCreateRoom} onOpenChange={setShowCreateRoom}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <UserPlus className="w-4 h-4 mr-2" />
                  创建房间
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>创建协作房间</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">房间名称</label>
                    <Input
                      value={newRoomName}
                      onChange={(e) => setNewRoomName(e.target.value)}
                      placeholder="输入房间名称"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">房间描述</label>
                    <Textarea
                      value={newRoomDescription}
                      onChange={(e) => setNewRoomDescription(e.target.value)}
                      placeholder="输入房间描述（可选）"
                      rows={3}
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="private"
                      checked={isPrivateRoom}
                      onChange={(e) => setIsPrivateRoom(e.target.checked)}
                    />
                    <label htmlFor="private" className="text-sm">私有房间</label>
                  </div>
                  <div className="flex justify-end space-x-2">
                    <Button variant="outline" onClick={() => setShowCreateRoom(false)}>
                      取消
                    </Button>
                    <Button onClick={createRoom}>
                      创建
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <ScrollArea className="h-full">
          <div className="p-2">
            {rooms.map((room) => (
              <div
                key={room.room_id}
                className={`p-3 rounded-lg cursor-pointer mb-2 transition-colors ${
                  currentRoom?.room_id === room.room_id
                    ? 'bg-blue-100 border-blue-200'
                    : 'hover:bg-gray-100'
                }`}
                onClick={() => joinRoom(room.room_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium">{room.name}</div>
                    <div className="text-sm text-gray-600">
                      {room.user_count} 人在线
                    </div>
                  </div>
                  {room.is_private && (
                    <Badge variant="secondary" size="sm">私有</Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* 聊天区域 */}
      <div className="flex-1 flex flex-col">
        {currentRoom ? (
          <>
            {/* 房间头部 */}
            <div className="p-4 border-b bg-white">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-semibold">{currentRoom.name}</h2>
                  <div className="text-sm text-gray-600">
                    {users.length} 人在线
                    {typingUsers.length > 0 && (
                      <span className="ml-2 text-blue-600">
                        {typingUsers.length} 人正在输入...
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {/* 语音通话控制 */}
                  <Button
                    variant={isInCall ? "destructive" : "outline"}
                    size="sm"
                    onClick={isInCall ? endVoiceCall : startVoiceCall}
                  >
                    {isInCall ? <PhoneOff className="w-4 h-4" /> : <Phone className="w-4 h-4" />}
                  </Button>
                  
                  {isInCall && (
                    <>
                      <Button
                        variant={isMuted ? "destructive" : "outline"}
                        size="sm"
                        onClick={() => setIsMuted(!isMuted)}
                      >
                        {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                      </Button>
                      
                      <Button
                        variant={isVideoOn ? "default" : "outline"}
                        size="sm"
                        onClick={() => setIsVideoOn(!isVideoOn)}
                      >
                        {isVideoOn ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
                      </Button>
                    </>
                  )}
                  
                  <Badge variant={isConnected ? "success" : "destructive"}>
                    {isConnected ? "已连接" : "未连接"}
                  </Badge>
                </div>
              </div>
            </div>

            {/* 消息列表 */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <div key={index} className={`flex ${
                    message.sender_id === currentUser?.id ? 'justify-end' : 'justify-start'
                  }`}>
                    {message.message_type === 'system' ? (
                      <div className="text-center text-sm text-gray-500 w-full">
                        {message.content.text}
                      </div>
                    ) : (
                      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.sender_id === currentUser?.id
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 text-gray-900'
                      }`}>
                        {message.sender_id !== currentUser?.id && (
                          <div className="text-xs opacity-75 mb-1">
                            {users.find(u => u.user_id === message.sender_id)?.username || '未知用户'}
                          </div>
                        )}
                        <div>{message.content.text}</div>
                        <div className={`text-xs mt-1 ${
                          message.sender_id === currentUser?.id ? 'text-blue-100' : 'text-gray-500'
                        }`}>
                          {formatTime(message.timestamp)}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* 消息输入 */}
            <div className="p-4 border-t bg-white">
              <div className="flex items-center space-x-2">
                <Input
                  value={messageInput}
                  onChange={(e) => {
                    setMessageInput(e.target.value);
                    startTyping();
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      sendMessage();
                    }
                  }}
                  placeholder="输入消息..."
                  disabled={!isConnected}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!isConnected || !messageInput.trim()}
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>选择一个房间开始协作</p>
            </div>
          </div>
        )}
      </div>

      {/* 用户列表 */}
      {currentRoom && (
        <div className="w-64 border-l bg-gray-50">
          <div className="p-4 border-b">
            <h3 className="font-semibold">在线用户 ({users.length})</h3>
          </div>
          <ScrollArea className="h-full">
            <div className="p-2">
              {users.map((user) => (
                <div key={user.user_id} className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100">
                  <div className="relative">
                    <Avatar className="w-8 h-8">
                      <AvatarImage src={user.avatar} />
                      <AvatarFallback>
                        {user.username.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white ${getUserStatusColor(user.status)}`} />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-sm">{user.username}</div>
                    {user.is_typing && (
                      <div className="text-xs text-blue-600">正在输入...</div>
                    )}
                  </div>
                  {user.user_id === currentRoom.created_by && (
                    <Crown className="w-4 h-4 text-yellow-500" />
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      )}
    </div>
  );
};

export default CollaborationInterface;
