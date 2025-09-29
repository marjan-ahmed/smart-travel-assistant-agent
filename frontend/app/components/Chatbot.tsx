'use client'
import React, { useState, useRef, useEffect } from 'react';

interface Message {
  sender: 'user' | 'bot';
  text: string;
  timestamp: Date;
}

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'bot',
      text: '👋 Hello! I\'m your Smart Travel Assistant. I can help you with travel planning, destinations, weather information, and restaurant recommendations. How can I assist you today?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMsg: Message = { 
      sender: 'user', 
      text: input.trim(),
      timestamp: new Date()
    };
    
    setMessages((msgs) => [...msgs, userMsg]);
    const currentInput = input.trim();
    setInput('');
    setLoading(true);
    
    try {
      const res = await fetch('/api/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: currentInput }),
      });
      const data = await res.json();
      
      setMessages((msgs) => [...msgs, { 
        sender: 'bot', 
        text: data.response,
        timestamp: new Date()
      }]);
    } catch (error) {
      setMessages((msgs) => [...msgs, { 
        sender: 'bot', 
        text: '❌ Sorry, I\'m having trouble connecting to my servers. Please try again in a moment.',
        timestamp: new Date()
      }]);
    }
    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const suggestedQuestions = [
    "What's the weather like in Tokyo?",
    "Find me restaurants in Paris",
    "Plan a 3-day trip to London",
    "Best attractions in New York"
  ];

  const handleSuggestionClick = (question: string) => {
    setInput(question);
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[85vh] border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 text-center">
        <h1 className="text-2xl font-bold flex items-center justify-center gap-2">
          ✈️ Smart Travel Assistant
        </h1>
        <p className="text-blue-100 text-sm mt-2">Your AI-powered travel companion</p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-gray-800">
        {messages.map((msg, i) => (
          <div key={i} className={`mb-6 flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
            <div className={`flex items-start gap-3 max-w-[80%] ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                msg.sender === 'user' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gradient-to-br from-purple-500 to-pink-500 text-white'
              }`}>
                {msg.sender === 'user' ? '👤' : '🤖'}
              </div>
              
              {/* Message Bubble */}
              <div className="flex flex-col">
                <div className={`px-4 py-3 rounded-2xl shadow-md ${
                  msg.sender === 'user' 
                    ? 'bg-blue-500 text-white rounded-tr-md' 
                    : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-tl-md border border-gray-200 dark:border-gray-600'
                }`}>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                </div>
                <span className={`text-xs text-gray-500 mt-1 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
                  {formatTime(msg.timestamp)}
                </span>
              </div>
            </div>
          </div>
        ))}
        
        {/* Loading indicator */}
        {loading && (
          <div className="mb-6 flex justify-start animate-fadeIn">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white flex items-center justify-center text-sm">
                🤖
              </div>
              <div className="bg-white dark:bg-gray-700 px-4 py-3 rounded-2xl rounded-tl-md shadow-md border border-gray-200 dark:border-gray-600">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {messages.length <= 1 && (
        <div className="px-6 py-4 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">💡 Try asking about:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, i) => (
              <button
                key={i}
                onClick={() => handleSuggestionClick(question)}
                className="px-3 py-2 text-sm bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors border border-blue-200 dark:border-blue-800"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-6 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <input
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 pr-12"
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me about travel destinations, weather, or restaurants..."
              disabled={loading}
              maxLength={500}
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-400">
              {input.length}/500
            </div>
          </div>
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-2xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:from-blue-600 hover:to-purple-700 transition-all duration-200 transform hover:scale-105 active:scale-95 shadow-lg"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              '📤'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
