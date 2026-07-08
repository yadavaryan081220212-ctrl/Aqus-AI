'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Plus, Settings, Menu, X, Bot, User, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { cn } from '@/lib/utils';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
}

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [useMemory, setUseMemory] = useState(true);
  const [useWebSearch, setUseWebSearch] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize with a new conversation
  useEffect(() => {
    if (conversations.length === 0) {
      const newConversation: Conversation = {
        id: Date.now().toString(),
        title: 'New Chat',
        messages: [],
      };
      setConversations([newConversation]);
      setActiveConversationId(newConversation.id);
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeConversationId, conversations]);

  const activeConversation = conversations.find((c) => c.id === activeConversationId);

  const createNewConversation = () => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
    };
    setConversations([newConversation, ...conversations]);
    setActiveConversationId(newConversation.id);
  };

  const browserCommands = (text: string): boolean => {
    const lowerText = text.toLowerCase();

    if (lowerText.startsWith('open youtube')) {
      window.open('https://youtube.com', '_blank');
      return true;
    }
    if (lowerText.startsWith('open google')) {
      window.open('https://google.com', '_blank');
      return true;
    }
    if (lowerText.startsWith('open gmail')) {
      window.open('https://mail.google.com', '_blank');
      return true;
    }
    if (lowerText.startsWith('open github')) {
      window.open('https://github.com', '_blank');
      return true;
    }
    if (lowerText.startsWith('open linkedin')) {
      window.open('https://linkedin.com', '_blank');
      return true;
    }
    return false;
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !activeConversationId) return;

    if (browserCommands(inputValue)) {
      setInputValue('');
      return;
    }

    const userMessage: Message = { role: 'user', content: inputValue };

    // Update conversation with user message
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === activeConversationId
          ? {
              ...conv,
              messages: [...conv.messages, userMessage],
              title: conv.title === 'New Chat' ? inputValue.slice(0, 30) : conv.title,
            }
          : conv
      )
    );

    setInputValue('');
    setIsTyping(true);

    try {
      const messagesToSend = useMemory
        ? [
            ...(activeConversation?.messages || []),
            userMessage,
          ]
        : [userMessage];

      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: messagesToSend,
          model: 'qwen2.5:0.5b',
          use_web_search: useWebSearch,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';

      // Add a placeholder for assistant message
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === activeConversationId
            ? {
                ...conv,
                messages: [...conv.messages, { role: 'assistant', content: '' }],
              }
            : conv
        )
      );

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              if (dataStr === '[DONE]') {
                break;
              }
              try {
                const data = JSON.parse(dataStr);
                if (data.content) {
                  assistantMessage += data.content;
                  setConversations((prev) =>
                    prev.map((conv) =>
                      conv.id === activeConversationId
                        ? {
                            ...conv,
                            messages: conv.messages.map((msg, idx) =>
                              idx === conv.messages.length - 1
                                ? { ...msg, content: assistantMessage }
                                : msg
                            ),
                          }
                        : conv
                    )
                  );
                }
              } catch (e) {
                // Ignore invalid JSON
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === activeConversationId
            ? {
                ...conv,
                messages: [
                  ...conv.messages,
                  { role: 'assistant', content: 'Sorry, something went wrong.' },
                ],
              }
            : conv
        )
      );
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <aside
        className={cn(
          'bg-card border-r border-border transition-all duration-300 flex flex-col',
          isSidebarOpen ? 'w-72' : 'w-0'
        )}
      >
        <div className="p-4 border-b border-border flex justify-between items-center">
          <h1 className="text-xl font-bold text-primary">aqus ai</h1>
          <button onClick={() => setIsSidebarOpen(false)} className="md:hidden">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4">
          <button
            onClick={createNewConversation}
            className="w-full bg-primary text-primary-foreground py-2 px-4 rounded-md flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
          >
            <Plus className="w-4 h-4" /> New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => setActiveConversationId(conv.id)}
              className={cn(
                'p-3 rounded-md cursor-pointer mb-2 transition-colors',
                activeConversationId === conv.id
                  ? 'bg-accent text-accent-foreground'
                  : 'hover:bg-muted'
              )}
            >
              <div className="text-sm truncate">{conv.title}</div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-border">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm text-mutedForeground">Memory</label>
              <button
                onClick={() => setUseMemory(!useMemory)}
                className={cn(
                  'w-10 h-6 rounded-full transition-colors',
                  useMemory ? 'bg-primary' : 'bg-muted'
                )}
              >
                <div
                  className={cn(
                    'w-4 h-4 bg-white rounded-full m-1 transition-transform',
                    useMemory ? 'translate-x-4' : 'translate-x-0'
                  )}
                />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm text-mutedForeground">Web Search</label>
              <button
                onClick={() => setUseWebSearch(!useWebSearch)}
                className={cn(
                  'w-10 h-6 rounded-full transition-colors',
                  useWebSearch ? 'bg-primary' : 'bg-muted'
                )}
              >
                <div
                  className={cn(
                    'w-4 h-4 bg-white rounded-full m-1 transition-transform',
                    useWebSearch ? 'translate-x-4' : 'translate-x-0'
                  )}
                />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b border-border p-4 flex items-center gap-4">
          {!isSidebarOpen && (
            <button onClick={() => setIsSidebarOpen(true)} className="md:hidden">
              <Menu className="w-6 h-6" />
            </button>
          )}
          <h2 className="text-lg font-semibold flex-1">
            {activeConversation?.title || 'aqus ai'}
          </h2>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="max-w-4xl mx-auto space-y-8">
            {activeConversation?.messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-20">
                <Bot className="w-24 h-24 text-primary mb-4" />
                <h2 className="text-2xl font-bold mb-2">How can I help you?</h2>
                <p className="text-mutedForeground max-w-md">
                  Ask me anything! Try commands like "Open YouTube" or "Search cat in YouTube"
                </p>
              </div>
            ) : (
              activeConversation?.messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={cn(
                    'flex gap-4',
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                      <Bot className="w-6 h-6 text-primaryForeground" />
                    </div>
                  )}
                  <div
                    className={cn(
                      'max-w-[80%]',
                      msg.role === 'user'
                        ? 'bg-primary text-primaryForeground p-4 rounded-2xl rounded-tr-sm'
                        : 'bg-card p-4 rounded-2xl rounded-tl-sm border border-border'
                    )}
                  >
                    {msg.role === 'assistant' ? (
                      <MarkdownRenderer content={msg.content} />
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                      <User className="w-6 h-6 text-secondaryForeground" />
                    </div>
                  )}
                </div>
              ))
            )}
            {isTyping && (
              <div className="flex gap-4 justify-start">
                <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                  <Bot className="w-6 h-6 text-primaryForeground" />
                </div>
                <div className="bg-card p-4 rounded-2xl rounded-tl-sm border border-border flex items-center gap-1">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-border p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                placeholder="Type your message here..."
                className="flex-1 bg-input border border-border rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isTyping}
                className="bg-primary text-primaryForeground py-3 px-6 rounded-md hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function MarkdownRenderer({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ node, inline, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <CodeBlock language={match[1]} value={String(children).replace(/\n$/, '')} />
          ) : (
            <code className={cn('bg-muted px-1.5 py-0.5 rounded text-sm', className)} {...props}>
              {children}
            </code>
          );
        },
        ul({ children }: { children?: React.ReactNode }) {
          return <ul className="list-disc ml-6 space-y-1">{children}</ul>;
        },
        ol({ children }: { children?: React.ReactNode }) {
          return <ol className="list-decimal ml-6 space-y-1">{children}</ol>;
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function CodeBlock({ language, value }: { language: string; value: string }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative my-4 rounded-md overflow-hidden">
      <div className="flex justify-between items-center bg-muted px-4 py-2">
        <span className="text-sm font-medium">{language}</span>
        <button onClick={copyToClipboard} className="flex items-center gap-1 text-sm hover:opacity-70">
          {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        customStyle={{ margin: 0, borderRadius: 0 }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
}
