'use client';

import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { MessageSquareText, Plus } from 'lucide-react';
import ChatInput from '@/components/chat/ChatInput';
import ChatMessage from '@/components/chat/ChatMessage';
import { useAiChat } from '@/lib/hooks/useAiChat';
import type { ChatMessage as ChatMessageType } from '@/lib/types/aiChat';

const conversationStorageKey = 'gov-ai-chat-conversation-id';
const messagesStorageKey = 'gov-ai-chat-messages';

const suggestedPrompts = [
  'Nợ công/GDP là gì?',
  'Top 10 nước có lạm phát CPI cao nhất năm 2020',
  'So sánh nợ công Việt Nam và Thái Lan từ 2010 đến 2023',
  'Phân tích lý do tại sao được không?',
  'Đổi sang năm 2021 và lấy top 5 thôi',
];

function createId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }

  return `chat-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function createConversationId() {
  return `conversation-${createId()}`;
}

function isChatMessage(value: unknown): value is ChatMessageType {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.id === 'string' &&
    (record.role === 'user' || record.role === 'assistant') &&
    typeof record.content === 'string' &&
    typeof record.createdAt === 'string'
  );
}

function readStoredMessages() {
  try {
    const raw = localStorage.getItem(messagesStorageKey);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter(isChatMessage).slice(-30) : [];
  } catch {
    return [];
  }
}

function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;

    if (typeof data === 'object' && data !== null && 'message' in data) {
      const message = (data as { message?: unknown }).message;
      return typeof message === 'string' ? message : error.message;
    }

    return error.message;
  }

  return error instanceof Error ? error.message : 'Không thể gửi câu hỏi tới trợ lý AI.';
}

export default function ChatPage() {
  const [conversationId, setConversationId] = useState('');
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState('');
  const [isHydrated, setIsHydrated] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const chatMutation = useAiChat();

  useEffect(() => {
    const storedConversationId = localStorage.getItem(conversationStorageKey);
    const nextConversationId = storedConversationId || createConversationId();

    localStorage.setItem(conversationStorageKey, nextConversationId);

    queueMicrotask(() => {
      setConversationId(nextConversationId);
      setMessages(readStoredMessages());
      setIsHydrated(true);
    });
  }, []);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    localStorage.setItem(messagesStorageKey, JSON.stringify(messages.slice(-30)));
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [isHydrated, messages]);

  async function handleSubmit() {
    const message = input.trim();

    if (!message || chatMutation.isPending) {
      return;
    }

    const activeConversationId = conversationId || createConversationId();
    if (!conversationId) {
      setConversationId(activeConversationId);
      localStorage.setItem(conversationStorageKey, activeConversationId);
    }

    setInput('');

    const userMessage: ChatMessageType = {
      id: createId(),
      role: 'user',
      content: message,
      createdAt: new Date().toISOString(),
      status: 'success',
    };

    setMessages((current) => [...current, userMessage].slice(-30));

    try {
      const response = await chatMutation.mutateAsync({
        message,
        conversationId: activeConversationId,
      });

      const assistantMessage: ChatMessageType = {
        id: createId(),
        role: 'assistant',
        content: response.answer || 'Không có phản hồi từ trợ lý AI.',
        createdAt: new Date().toISOString(),
        response,
        status: 'success',
      };

      setMessages((current) => [...current, assistantMessage].slice(-30));
    } catch (error) {
      const assistantMessage: ChatMessageType = {
        id: createId(),
        role: 'assistant',
        content: 'Không thể nhận phản hồi từ trợ lý AI.',
        createdAt: new Date().toISOString(),
        status: 'error',
        error: getErrorMessage(error),
      };

      setMessages((current) => [...current, assistantMessage].slice(-30));
    }
  }

  function handleNewChat() {
    const nextConversationId = createConversationId();
    setConversationId(nextConversationId);
    setMessages([]);
    setInput('');
    localStorage.setItem(conversationStorageKey, nextConversationId);
    localStorage.removeItem(messagesStorageKey);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Trợ lý AI dữ liệu</h1>
          <p className="mt-1 text-sm text-slate-600">
            Hỏi về nợ công, lạm phát CPI, tăng trưởng GDP, thất nghiệp và so sánh dữ liệu vĩ mô.
          </p>
        </div>
        <button
          type="button"
          onClick={handleNewChat}
          className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:border-blue-300 hover:text-blue-700"
        >
          <Plus className="h-4 w-4" />
          New chat
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
        <section className="flex min-h-[680px] flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="flex-1 space-y-4 overflow-y-auto bg-slate-50 p-4">
            {messages.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <div className="max-w-md text-center">
                  <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-blue-50 text-blue-600">
                    <MessageSquareText className="h-5 w-5" />
                  </div>
                  <h2 className="text-base font-semibold text-slate-900">Bắt đầu phân tích bằng câu hỏi tự nhiên</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    Dùng cùng cuộc hội thoại để hỏi tiếp, phân tích lý do hoặc đổi năm và giới hạn kết quả.
                  </p>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <ChatMessage key={message.id} message={message} onClarificationClick={setInput} />
              ))
            )}

            {chatMutation.isPending ? (
              <div className="flex justify-start">
                <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
                  Đang xử lý câu hỏi...
                </div>
              </div>
            ) : null}
            <div ref={bottomRef} />
          </div>

          <ChatInput value={input} isLoading={chatMutation.isPending} onChange={setInput} onSubmit={handleSubmit} />
        </section>

        <aside className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-900">Gợi ý câu hỏi</h2>
            <div className="mt-3 space-y-2">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => setInput(prompt)}
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-left text-sm text-slate-700 hover:border-blue-300 hover:bg-blue-50"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs text-slate-500 shadow-sm">
            <div className="font-medium text-slate-700">Conversation ID</div>
            <div className="mt-1 break-all">{conversationId || 'Đang khởi tạo...'}</div>
          </div>
        </aside>
      </div>
    </div>
  );
}
