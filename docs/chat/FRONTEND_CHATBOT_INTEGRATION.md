# Frontend Integration Guide: Telegram-like Chat Bot

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [WebSocket Integration](#websocket-integration)
- [Chat Bot API Integration](#chat-bot-api-integration)
- [UI Components with shadcn/ui](#ui-components-with-shadcnui)
- [Complete Implementation](#complete-implementation)
- [State Management](#state-management)
- [Best Practices](#best-practices)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This guide provides step-by-step instructions for frontend developers to integrate Pycelize's **Telegram-like Chat Bot** and **Chat Workflow** features into your web application.

### What You'll Build

A modern chat interface similar to Telegram that allows users to:

- 💬 **Chat with AI Bot** - Natural language file processing
- 📁 **Upload Files** - Drag-and-drop or click to upload
- 🔄 **Real-time Progress** - Live updates via WebSocket
- ✅ **Confirm Workflows** - Review and modify before execution
- 📥 **Download Results** - One-click file downloads
- 📜 **View History** - Complete conversation history

### Tech Stack

- **UI Framework**: shadcn/ui (Radix UI + Tailwind CSS)
- **WebSocket**: Native WebSocket API with your existing `websocket-manager`
- **API Client**: fetch/axios for REST endpoints
- **State**: React Context API or Zustand

---

## 📚 Prerequisites

Before you start, ensure you have:

1. **Backend Running**:

   ```bash
   # REST API on port 5050
   http://localhost:5050/api/v1/chat/bot/conversations

   # WebSocket on port 5051
   ws://localhost:5051/chat/{chat_id}
   ```

2. **Frontend Setup**:
   - React 18+ (or Vue/Angular equivalent)
   - shadcn/ui installed
   - Tailwind CSS configured
   - Your existing `websocket-manager` class

3. **Required shadcn/ui Components**:
   ```bash
   npx shadcn-ui@latest add button
   npx shadcn-ui@latest add input
   npx shadcn-ui@latest add card
   npx shadcn-ui@latest add avatar
   npx shadcn-ui@latest add badge
   npx shadcn-ui@latest add scroll-area
   npx shadcn-ui@latest add separator
   npx shadcn-ui@latest add dialog
   npx shadcn-ui@latest add progress
   npx shadcn-ui@latest add toast
   ```

---

## 🚀 Quick Start

### 1. Create a New Chat Conversation

```typescript
// api/chatbot.ts
const API_BASE = "http://localhost:5050/api/v1";

export async function createChatConversation() {
  const response = await fetch(`${API_BASE}/chat/bot/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });

  const data = await response.json();
  return data.data; // { chat_id, participant_name, bot_message, ... }
}
```

### 2. Connect to WebSocket

```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef } from "react";
import { WebSocketManager } from "@/lib/websocket-manager"; // Your existing class

export function useChatWebSocket(
  chatId: string,
  onMessage: (msg: any) => void,
) {
  const wsManager = useRef<WebSocketManager | null>(null);

  useEffect(() => {
    if (!chatId) return;

    // Reuse your existing WebSocket manager
    wsManager.current = new WebSocketManager({
      url: `ws://localhost:5051/chat/${chatId}`,
      onMessage: onMessage,
      onError: (error) => console.error("WebSocket error:", error),
      reconnect: true,
      reconnectInterval: 3000,
    });

    wsManager.current.connect();

    return () => {
      wsManager.current?.disconnect();
    };
  }, [chatId, onMessage]);

  return wsManager.current;
}
```

### 3. Basic Chat Component

```tsx
// components/ChatBot.tsx
import { useState, useEffect } from "react";
import { createChatConversation } from "@/api/chatbot";
import { useChatWebSocket } from "@/hooks/useWebSocket";
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";

export function ChatBot() {
  const [chatId, setChatId] = useState<string>("");
  const [messages, setMessages] = useState<any[]>([]);

  useEffect(() => {
    // Initialize chat on component mount
    createChatConversation().then((data) => {
      setChatId(data.chat_id);
      setMessages([
        {
          type: "system",
          content: data.bot_message,
          timestamp: new Date(),
        },
      ]);
    });
  }, []);

  const handleWebSocketMessage = (msg: any) => {
    console.log("WebSocket message:", msg);
    // Handle progress updates, workflow events, etc.
  };

  useChatWebSocket(chatId, handleWebSocketMessage);

  return (
    <div className="flex flex-col h-screen">
      <ChatMessages messages={messages} />
      <ChatInput chatId={chatId} />
    </div>
  );
}
```

---

## 🔌 WebSocket Integration

### Reusing Your Existing WebSocket Manager

Your frontend already has a `websocket-manager` class. Here's how to integrate it with the chat bot:

```typescript
// lib/websocket-manager.ts (Your existing class)
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private onMessage: (data: any) => void;
  private onError: (error: Event) => void;
  private reconnect: boolean;
  private reconnectInterval: number;

  constructor(config: WebSocketConfig) {
    this.url = config.url;
    this.onMessage = config.onMessage;
    this.onError = config.onError;
    this.reconnect = config.reconnect ?? true;
    this.reconnectInterval = config.reconnectInterval ?? 3000;
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log("✅ WebSocket connected");
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.onMessage(data);
    };

    this.ws.onerror = (error) => {
      this.onError(error);
    };

    this.ws.onclose = () => {
      console.log("❌ WebSocket closed");
      if (this.reconnect) {
        setTimeout(() => this.connect(), this.reconnectInterval);
      }
    };
  }

  disconnect() {
    this.reconnect = false;
    this.ws?.close();
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}
```

### WebSocket Message Types

The backend sends these message types:

#### 1. Connected (Welcome)

```typescript
{
  type: "connected",
  chat_id: "550e8400-...",
  message: "Connected to chat workflow"
}
```

#### 2. Workflow Started

```typescript
{
  type: "workflow_started",
  chat_id: "550e8400-...",
  total_steps: 3,
  message: "🚀 Starting workflow execution..."
}
```

#### 3. Progress Update

```typescript
{
  type: "progress",
  chat_id: "550e8400-...",
  step_id: "step-1",
  operation: "excel/extract-columns-to-file",
  progress: 45,
  status: "running",
  message: "Processing column 'customer_id'"
}
```

#### 4. Workflow Completed

```typescript
{
  type: "workflow_completed",
  chat_id: "550e8400-...",
  total_steps: 3,
  output_files_count: 2,
  message: "✅ Workflow completed successfully!"
}
```

#### 5. Workflow Failed

```typescript
{
  type: "workflow_failed",
  chat_id: "550e8400-...",
  error: "Operation failed: Invalid column name",
  message: "❌ Workflow execution failed"
}
```

### Handling WebSocket Messages

```typescript
// hooks/useChatWebSocket.ts
import { useCallback } from "react";
import { useToast } from "@/components/ui/use-toast";

export function useWebSocketHandler(
  onProgress: (progress: number, message: string) => void,
  onComplete: (message: string) => void,
  onError: (error: string) => void,
) {
  const { toast } = useToast();

  const handleMessage = useCallback(
    (msg: any) => {
      switch (msg.type) {
        case "connected":
          console.log("✅ Connected to chat:", msg.chat_id);
          break;

        case "workflow_started":
          toast({
            title: "Workflow Started",
            description: `Processing ${msg.total_steps} steps...`,
          });
          onProgress(0, msg.message);
          break;

        case "progress":
          onProgress(msg.progress, msg.message);
          break;

        case "workflow_completed":
          toast({
            title: "Success!",
            description: msg.message,
            variant: "success",
          });
          onComplete(msg.message);
          break;

        case "workflow_failed":
          toast({
            title: "Workflow Failed",
            description: msg.error,
            variant: "destructive",
          });
          onError(msg.error);
          break;

        case "pong":
          // Keepalive response
          break;

        default:
          console.log("Unknown message type:", msg.type);
      }
    },
    [onProgress, onComplete, onError, toast],
  );

  return handleMessage;
}
```

### Keepalive Ping/Pong

```typescript
// Send ping every 30 seconds to keep connection alive
useEffect(() => {
  if (!wsManager) return;

  const interval = setInterval(() => {
    wsManager.send({ type: "ping" });
  }, 30000);

  return () => clearInterval(interval);
}, [wsManager]);
```

---

## 🤖 Chat Bot API Integration

### API Client Setup

```typescript
// api/chatbot.ts
const API_BASE = "http://localhost:5050/api/v1";

export const chatBotAPI = {
  // 1. Create conversation
  async createConversation() {
    const response = await fetch(`${API_BASE}/chat/bot/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const data = await response.json();
    return data.data;
  },

  // 2. Send message
  async sendMessage(chatId: string, message: string) {
    const response = await fetch(
      `${API_BASE}/chat/bot/conversations/${chatId}/message`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      },
    );
    const data = await response.json();
    return data.data;
  },

  // 3. Upload file
  async uploadFile(chatId: string, file: File) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
      `${API_BASE}/chat/bot/conversations/${chatId}/upload`,
      {
        method: "POST",
        body: formData,
      },
    );
    const data = await response.json();
    return data.data;
  },

  // 4. Confirm workflow
  async confirmWorkflow(
    chatId: string,
    confirmed: boolean,
    modifiedWorkflow?: any[],
  ) {
    const response = await fetch(
      `${API_BASE}/chat/bot/conversations/${chatId}/confirm`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          confirmed,
          modified_workflow: modifiedWorkflow,
        }),
      },
    );
    const data = await response.json();
    return data.data;
  },

  // 5. Get history
  async getHistory(chatId: string, limit?: number) {
    const url = new URL(`${API_BASE}/chat/bot/conversations/${chatId}/history`);
    if (limit) url.searchParams.set("limit", limit.toString());

    const response = await fetch(url.toString());
    const data = await response.json();
    return data.data;
  },

  // 6. Delete conversation
  async deleteConversation(chatId: string) {
    const response = await fetch(
      `${API_BASE}/chat/bot/conversations/${chatId}`,
      { method: "DELETE" },
    );
    const data = await response.json();
    return data.data;
  },

  // 7. Get supported operations
  async getSupportedOperations() {
    const response = await fetch(`${API_BASE}/chat/bot/operations`);
    const data = await response.json();
    return data.data;
  },
};
```

### Message Flow

```typescript
// hooks/useChatBot.ts
import { useState, useCallback } from "react";
import { chatBotAPI } from "@/api/chatbot";

export function useChatBot() {
  const [chatId, setChatId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pendingWorkflow, setPendingWorkflow] = useState<any>(null);

  // Initialize chat
  const initChat = useCallback(async () => {
    const data = await chatBotAPI.createConversation();
    setChatId(data.chat_id);

    // Add welcome message
    setMessages([
      {
        id: "1",
        type: "system",
        content: data.bot_message,
        timestamp: new Date(data.created_at),
      },
    ]);

    return data.chat_id;
  }, []);

  // Send text message
  const sendMessage = useCallback(
    async (text: string) => {
      if (!chatId || !text.trim()) return;

      // Add user message to UI
      const userMessage = {
        id: Date.now().toString(),
        type: "user" as const,
        content: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      setIsLoading(true);
      try {
        const data = await chatBotAPI.sendMessage(chatId, text);

        // Add bot response
        const botMessage = {
          id: (Date.now() + 1).toString(),
          type: "system" as const,
          content: data.bot_response,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, botMessage]);

        // Store pending workflow if confirmation required
        if (data.requires_confirmation && data.suggested_workflow) {
          setPendingWorkflow(data.suggested_workflow);
        }
      } catch (error) {
        console.error("Failed to send message:", error);
      } finally {
        setIsLoading(false);
      }
    },
    [chatId],
  );

  // Upload file
  const uploadFile = useCallback(
    async (file: File) => {
      if (!chatId) return;

      setIsLoading(true);
      try {
        const data = await chatBotAPI.uploadFile(chatId, file);

        // Add file upload message
        const fileMessage = {
          id: Date.now().toString(),
          type: "file" as const,
          content: `📎 Uploaded: ${file.name}`,
          file: {
            name: file.name,
            url: data.download_url,
          },
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, fileMessage]);

        // Add bot response
        if (data.bot_response) {
          const botMessage = {
            id: (Date.now() + 1).toString(),
            type: "system" as const,
            content: data.bot_response,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, botMessage]);
        }

        // Store pending workflow
        if (data.requires_confirmation && data.suggested_workflow) {
          setPendingWorkflow(data.suggested_workflow);
        }
      } catch (error) {
        console.error("Failed to upload file:", error);
      } finally {
        setIsLoading(false);
      }
    },
    [chatId],
  );

  // Confirm workflow
  const confirmWorkflow = useCallback(
    async (confirmed: boolean, modified?: any[]) => {
      if (!chatId) return;

      setIsLoading(true);
      try {
        const data = await chatBotAPI.confirmWorkflow(
          chatId,
          confirmed,
          modified || pendingWorkflow,
        );

        // Add confirmation message
        const confirmMessage = {
          id: Date.now().toString(),
          type: "user" as const,
          content: confirmed ? "✅ Yes, proceed" : "❌ No, cancel",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, confirmMessage]);

        // Clear pending workflow
        setPendingWorkflow(null);

        // Add bot response
        if (data.bot_response) {
          const botMessage = {
            id: (Date.now() + 1).toString(),
            type: "system" as const,
            content: data.bot_response,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, botMessage]);
        }

        return data;
      } catch (error) {
        console.error("Failed to confirm workflow:", error);
      } finally {
        setIsLoading(false);
      }
    },
    [chatId, pendingWorkflow],
  );

  return {
    chatId,
    messages,
    isLoading,
    pendingWorkflow,
    initChat,
    sendMessage,
    uploadFile,
    confirmWorkflow,
  };
}
```

---

## 🎨 UI Components with shadcn/ui

### 1. Chat Message Component

```tsx
// components/ChatMessage.tsx
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import { Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface ChatMessageProps {
  message: {
    id: string;
    type: "user" | "system" | "file";
    content: string;
    timestamp: Date;
    file?: {
      name: string;
      url: string;
    };
  };
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.type === "user";
  const isSystem = message.type === "system";

  return (
    <div
      className={cn(
        "flex gap-3 mb-4",
        isUser ? "flex-row-reverse" : "flex-row",
      )}
    >
      {/* Avatar */}
      <Avatar className="h-8 w-8">
        <AvatarFallback className={cn(isUser ? "bg-blue-500" : "bg-green-500")}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      {/* Message Bubble */}
      <Card
        className={cn(
          "p-3 max-w-[70%]",
          isUser ? "bg-blue-500 text-white" : "bg-muted",
        )}
      >
        {/* File attachment */}
        {message.file && (
          <a
            href={message.file.url}
            download
            className="flex items-center gap-2 mb-2 text-sm hover:underline"
          >
            📎 {message.file.name}
          </a>
        )}

        {/* Message content with Markdown support */}
        <div className="prose prose-sm dark:prose-invert">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {/* Timestamp */}
        <div
          className={cn(
            "text-xs mt-2 opacity-70",
            isUser ? "text-right" : "text-left",
          )}
        >
          {message.timestamp.toLocaleTimeString()}
        </div>
      </Card>
    </div>
  );
}
```

### 2. Chat Input Component

```tsx
// components/ChatInput.tsx
import { useState, useRef, KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Paperclip, Send } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onUploadFile: (file: File) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSendMessage,
  onUploadFile,
  disabled,
  placeholder = "Type a message...",
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUploadFile(file);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="border-t p-4 bg-background">
      <div className="flex gap-2">
        {/* File upload button */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          disabled={disabled}
          onClick={() => fileInputRef.current?.click()}
        >
          <Paperclip className="h-4 w-4" />
        </Button>

        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileSelect}
          accept=".xlsx,.xls,.csv"
        />

        {/* Message input */}
        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="flex-1"
        />

        {/* Send button */}
        <Button
          onClick={handleSubmit}
          disabled={disabled || !message.trim()}
          size="icon"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
```

### 3. Workflow Confirmation Dialog

```tsx
// components/WorkflowConfirmDialog.tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle } from "lucide-react";

interface WorkflowConfirmDialogProps {
  open: boolean;
  workflow: Array<{
    operation: string;
    arguments: any;
    description?: string;
  }>;
  onConfirm: () => void;
  onCancel: () => void;
}

export function WorkflowConfirmDialog({
  open,
  workflow,
  onConfirm,
  onCancel,
}: WorkflowConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Confirm Workflow</DialogTitle>
          <DialogDescription>
            Review the suggested workflow before execution
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 my-4">
          {workflow?.map((step, index) => (
            <div key={index} className="border rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline">Step {index + 1}</Badge>
                <span className="font-medium">{step.operation}</span>
              </div>

              {step.description && (
                <p className="text-sm text-muted-foreground mb-2">
                  {step.description}
                </p>
              )}

              <div className="bg-muted p-3 rounded text-sm">
                <pre className="overflow-x-auto">
                  {JSON.stringify(step.arguments, null, 2)}
                </pre>
              </div>
            </div>
          ))}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            <XCircle className="h-4 w-4 mr-2" />
            Cancel
          </Button>
          <Button onClick={onConfirm}>
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Confirm & Execute
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### 4. Progress Indicator

```tsx
// components/WorkflowProgress.tsx
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

interface WorkflowProgressProps {
  operation?: string;
  progress: number;
  status: string;
  message: string;
}

export function WorkflowProgress({
  operation,
  progress,
  status,
  message,
}: WorkflowProgressProps) {
  return (
    <Card className="p-4 mb-4">
      <div className="flex items-center gap-2 mb-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="font-medium">Processing...</span>
        <Badge variant={status === "running" ? "default" : "secondary"}>
          {status}
        </Badge>
      </div>

      {operation && (
        <p className="text-sm text-muted-foreground mb-2">{operation}</p>
      )}

      <Progress value={progress} className="mb-2" />

      <p className="text-xs text-muted-foreground">{message}</p>
    </Card>
  );
}
```

### 5. Chat Messages Container

```tsx
// components/ChatMessages.tsx
import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import { WorkflowProgress } from "./WorkflowProgress";

interface ChatMessagesProps {
  messages: any[];
  workflowProgress?: {
    operation: string;
    progress: number;
    status: string;
    message: string;
  };
}

export function ChatMessages({
  messages,
  workflowProgress,
}: ChatMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, workflowProgress]);

  return (
    <ScrollArea className="flex-1 p-4" ref={scrollRef}>
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}

      {workflowProgress && <WorkflowProgress {...workflowProgress} />}
    </ScrollArea>
  );
}
```

---

## 💻 Complete Implementation

### Full Chat Bot Page

```tsx
// app/chat/page.tsx
"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { useChatBot } from "@/hooks/useChatBot";
import { useChatWebSocket } from "@/hooks/useWebSocket";
import { useWebSocketHandler } from "@/hooks/useWebSocketHandler";
import { ChatMessages } from "@/components/ChatMessages";
import { ChatInput } from "@/components/ChatInput";
import { WorkflowConfirmDialog } from "@/components/WorkflowConfirmDialog";

export default function ChatBotPage() {
  const {
    chatId,
    messages,
    isLoading,
    pendingWorkflow,
    initChat,
    sendMessage,
    uploadFile,
    confirmWorkflow,
  } = useChatBot();

  const [workflowProgress, setWorkflowProgress] = useState<any>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // Initialize chat on mount
  useEffect(() => {
    initChat();
  }, [initChat]);

  // Show workflow confirmation dialog when workflow is pending
  useEffect(() => {
    if (pendingWorkflow) {
      setShowConfirmDialog(true);
    }
  }, [pendingWorkflow]);

  // WebSocket message handler
  const handleWebSocketMessage = useWebSocketHandler(
    (progress, message) => {
      setWorkflowProgress({ progress, message, status: "running" });
    },
    (message) => {
      setWorkflowProgress(null);
      // Workflow completed - could refresh history here
    },
    (error) => {
      setWorkflowProgress(null);
      console.error("Workflow error:", error);
    },
  );

  useChatWebSocket(chatId, handleWebSocketMessage);

  const handleConfirmWorkflow = async () => {
    setShowConfirmDialog(false);
    await confirmWorkflow(true);
  };

  const handleCancelWorkflow = async () => {
    setShowConfirmDialog(false);
    await confirmWorkflow(false);
  };

  return (
    <div className="container mx-auto h-screen p-4">
      <Card className="h-full flex flex-col">
        {/* Header */}
        <div className="p-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Pycelize Chat Bot</h1>
            <p className="text-sm text-muted-foreground">
              Chat ID: {chatId || "Connecting..."}
            </p>
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => window.location.reload()}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        <Separator />

        {/* Messages */}
        <ChatMessages messages={messages} workflowProgress={workflowProgress} />

        <Separator />

        {/* Input */}
        <ChatInput
          onSendMessage={sendMessage}
          onUploadFile={uploadFile}
          disabled={isLoading}
          placeholder={
            isLoading ? "Processing..." : "Ask me to process your files..."
          }
        />
      </Card>

      {/* Workflow Confirmation Dialog */}
      <WorkflowConfirmDialog
        open={showConfirmDialog}
        workflow={pendingWorkflow || []}
        onConfirm={handleConfirmWorkflow}
        onCancel={handleCancelWorkflow}
      />
    </div>
  );
}
```

---

## 🗂️ State Management

### Option 1: React Context

```typescript
// contexts/ChatContext.tsx
import { createContext, useContext, useState, ReactNode } from 'react';

interface ChatContextType {
  chatId: string;
  setChatId: (id: string) => void;
  messages: Message[];
  addMessage: (message: Message) => void;
  // ... other state and methods
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [chatId, setChatId] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);

  const addMessage = (message: Message) => {
    setMessages(prev => [...prev, message]);
  };

  return (
    <ChatContext.Provider value={{
      chatId,
      setChatId,
      messages,
      addMessage
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within ChatProvider');
  }
  return context;
};
```

### Option 2: Zustand Store

```typescript
// stores/chatStore.ts
import { create } from "zustand";

interface ChatState {
  chatId: string;
  messages: Message[];
  isLoading: boolean;
  pendingWorkflow: any;

  setChatId: (id: string) => void;
  addMessage: (message: Message) => void;
  setLoading: (loading: boolean) => void;
  setPendingWorkflow: (workflow: any) => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  chatId: "",
  messages: [],
  isLoading: false,
  pendingWorkflow: null,

  setChatId: (id) => set({ chatId: id }),
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  setLoading: (loading) => set({ isLoading: loading }),
  setPendingWorkflow: (workflow) => set({ pendingWorkflow: workflow }),
  reset: () =>
    set({
      chatId: "",
      messages: [],
      isLoading: false,
      pendingWorkflow: null,
    }),
}));
```

---

## ✨ Best Practices

### 1. Error Handling

```typescript
// utils/errorHandler.ts
import { toast } from "@/components/ui/use-toast";

export function handleAPIError(error: any) {
  const message = error?.message || "An error occurred";

  toast({
    title: "Error",
    description: message,
    variant: "destructive",
  });

  console.error("API Error:", error);
}

// Usage
try {
  await chatBotAPI.sendMessage(chatId, message);
} catch (error) {
  handleAPIError(error);
}
```

### 2. Loading States

```typescript
// Use skeleton loaders during initial load
{isLoading && <ChatMessageSkeleton />}
{!isLoading && messages.map(...)}

// Disable inputs during processing
<ChatInput
  disabled={isLoading || workflowProgress !== null}
  placeholder={
    isLoading ? 'Processing...' :
    workflowProgress ? 'Workflow in progress...' :
    'Type a message...'
  }
/>
```

### 3. Optimistic Updates

```typescript
// Add message immediately (optimistic)
const optimisticMessage = {
  id: Date.now().toString(),
  type: "user",
  content: text,
  timestamp: new Date(),
  pending: true, // Mark as pending
};
setMessages((prev) => [...prev, optimisticMessage]);

// Then send to server
try {
  const response = await chatBotAPI.sendMessage(chatId, text);
  // Update with server response
  setMessages((prev) =>
    prev.map((msg) =>
      msg.id === optimisticMessage.id ? { ...msg, pending: false } : msg,
    ),
  );
} catch (error) {
  // Remove on error
  setMessages((prev) => prev.filter((msg) => msg.id !== optimisticMessage.id));
}
```

### 4. Reconnection Strategy

```typescript
// Implement exponential backoff for WebSocket reconnection
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

const reconnect = () => {
  if (reconnectAttempts >= maxReconnectAttempts) {
    toast({
      title: "Connection Lost",
      description: "Unable to reconnect. Please refresh the page.",
      variant: "destructive",
    });
    return;
  }

  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
  reconnectAttempts++;

  setTimeout(() => {
    wsManager.connect();
  }, delay);
};
```

### 5. File Upload Progress

```typescript
// Show upload progress for large files
const uploadFileWithProgress = async (file: File) => {
  const xhr = new XMLHttpRequest();

  return new Promise((resolve, reject) => {
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        const percent = (e.loaded / e.total) * 100;
        setUploadProgress(percent);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status === 200) {
        resolve(JSON.parse(xhr.response));
      } else {
        reject(new Error("Upload failed"));
      }
    });

    xhr.open("POST", `${API_BASE}/chat/bot/conversations/${chatId}/upload`);

    const formData = new FormData();
    formData.append("file", file);
    xhr.send(formData);
  });
};
```

---

## 🧪 Testing

### Test Checklist

- [ ] Chat initialization works
- [ ] WebSocket connects and receives messages
- [ ] Can send text messages
- [ ] Can upload files
- [ ] Workflow confirmation dialog appears
- [ ] Can confirm/decline workflows
- [ ] Progress updates display correctly
- [ ] Can download result files
- [ ] History loads correctly
- [ ] Reconnection works after disconnect
- [ ] Error states display properly
- [ ] Mobile responsive

### Testing Script

```typescript
// test/chatbot.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatBotPage } from '@/app/chat/page';

describe('ChatBot', () => {
  it('initializes chat conversation', async () => {
    render(<ChatBotPage />);

    await waitFor(() => {
      expect(screen.getByText(/Welcome to Pycelize/)).toBeInTheDocument();
    });
  });

  it('sends message and receives response', async () => {
    render(<ChatBotPage />);
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText(/Type a message/);
    await user.type(input, 'extract columns: name, email');

    const sendButton = screen.getByRole('button', { name: /send/i });
    await user.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/extract columns/)).toBeInTheDocument();
    });
  });

  // Add more tests...
});
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. WebSocket Connection Fails

**Problem**: `WebSocket connection to 'ws://localhost:5051' failed`

**Solutions**:

- Check if WebSocket server is running on port 5051
- Verify firewall settings
- Use correct protocol (ws:// for http, wss:// for https)

```typescript
// Check WebSocket readiness
if (ws.readyState === WebSocket.OPEN) {
  console.log("✅ WebSocket connected");
} else {
  console.log("❌ WebSocket not ready:", ws.readyState);
}
```

#### 2. CORS Errors

**Problem**: `Access to fetch blocked by CORS policy`

**Solution**: Backend must allow your frontend origin

```python
# Backend: app/__init__.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])
```

#### 3. Messages Not Persisting

**Problem**: History endpoint returns empty messages

**Solution**: This was fixed in recent updates. Ensure you're using latest backend version.

#### 4. File Upload Fails

**Problem**: File upload returns 413 (Payload Too Large)

**Solution**: Increase max file size in backend config

```yaml
# configs/application.yml
upload:
  max_size: 100MB # Increase as needed
```

#### 5. Workflow Progress Not Showing

**Problem**: No progress updates during workflow execution

**Solutions**:

- Verify WebSocket is connected before starting workflow
- Check browser console for WebSocket messages
- Ensure correct chat_id is used

```typescript
// Debug WebSocket messages
wsManager.onMessage = (msg) => {
  console.log("📩 WS Message:", msg);
  handleMessage(msg);
};
```

---

## 📚 Additional Resources

### Documentation

- [FRONTEND_CHATBOT_README.md](../FRONTEND_CHATBOT_README.md) - Complete API reference
- [BACKEND_CHATBOT.md](../BACKEND_CHATBOT.md) - Backend architecture
- [WEBSOCKET_USAGE.md](./WEBSOCKET_USAGE.md) - WebSocket details

### shadcn/ui Resources

- [shadcn/ui Documentation](https://ui.shadcn.com/)
- [Radix UI Primitives](https://www.radix-ui.com/)
- [Tailwind CSS](https://tailwindcss.com/)

### Example Projects

- Check `tests/` directory for integration tests
- See `app/api/routes/chatbot_routes.py` for API implementation

---

## 🤝 Need Help?

If you encounter issues not covered here:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review backend logs for error details
3. Test API endpoints with cURL first
4. Verify WebSocket connection in browser DevTools
5. Open an issue on GitHub with reproduction steps

---

**Happy Coding! 🚀**
