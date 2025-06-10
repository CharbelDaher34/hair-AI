import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Send, Bot, User, Sparkles, TrendingUp, Users, FileText } from "lucide-react";
import { toast } from "@/hooks/use-toast";

interface Message {
  id: number;
  type: "user" | "bot";
  content: string;
  timestamp: Date;
}

const ChatBot = () => {
  const [messages, setMessages] = useState<Message[]>([
    // {
    //   id: 1,
    //   type: "bot",
    //   content: "Hello! I'm your HR AI Assistant. I can help you with analytics, candidate insights, job performance data, and recruitment trends. What would you like to know?",
    //   timestamp: new Date(),
    // },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      toast({
        title: "Authentication Error",
        description: "You must be logged in to use the chat.",
        variant: "destructive",
      });
      // maybe redirect to login page
      return;
    }

    // Connect to the WebSocket server
    ws.current = new WebSocket("ws://84.16.230.94:8017/api/v1/ws");

    ws.current.onopen = () => {
      console.log("WebSocket connected");
      // Send the token for authentication
      ws.current?.send(token);
      setIsTyping(true); // Show typing indicator while waiting for initial message
    };

    ws.current.onmessage = (event) => {
        setMessages(prev => [...prev, {
            id: prev.length + 1,
            type: "bot",
            content: event.data,
            timestamp: new Date(),
        }]);
        setIsTyping(false);
    };

    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      toast({
        title: "Connection Error",
        description: "Could not connect to the chat service.",
        variant: "destructive",
      });
      setIsTyping(false);
    };

    ws.current.onclose = () => {
      console.log("WebSocket disconnected");
      setIsTyping(false);
    };

    // Clean up the connection when the component unmounts
    return () => {
      ws.current?.close();
    };
  }, []); // Empty dependency array means this effect runs once on mount

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const quickQuestions = [
    "Show me this month's application trends",
    "Which jobs have the highest conversion rates?",
    "What are the top candidate drop-off points?",
    "Compare interview success rates by position",
  ];

  const handleSendMessage = async () => {
    if (!input.trim() || !ws.current || ws.current.readyState !== WebSocket.OPEN) return;

    const userMessage: Message = {
      id: messages.length + 1,
      type: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    
    // Send message to the server
    ws.current.send(input);

    setInput("");
    setIsTyping(true);
  };

  const handleQuickQuestion = (question: string) => {
    setInput(question);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight flex items-center gap-3 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            <Sparkles className="h-10 w-10 text-blue-600" />
            AI Assistant
          </h1>
          <p className="text-lg text-gray-600">
            Get insights and analytics from your HR data using natural language
          </p>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-4">
        <div className="lg:col-span-3">
          <Card className="h-[650px] flex flex-col card shadow-xl hover:shadow-2xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
                <div className="p-2 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg">
                  <Bot className="h-6 w-6 text-blue-600" />
                </div>
                Chat Assistant
              </CardTitle>
              <CardDescription className="text-base text-gray-600">
                Ask questions about your recruitment data and get AI-powered insights
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <ScrollArea className="flex-1 pr-4">
                <div className="space-y-6">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex items-start space-x-4 ${
                        message.type === "user" ? "flex-row-reverse space-x-reverse" : ""
                      }`}
                    >
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center shadow-md ${
                        message.type === "user" 
                          ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white" 
                          : "bg-gradient-to-r from-gray-100 to-blue-100 text-gray-700"
                      }`}>
                        {message.type === "user" ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                      </div>
                      <div className={`max-w-[80%] p-4 rounded-2xl shadow-md ${
                        message.type === "user"
                          ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white ml-auto"
                          : "bg-white border border-gray-200"
                      }`}>
                        <div className={`prose prose-sm max-w-none ${
                          message.type === "user" 
                            ? "prose-invert" 
                            : "prose-gray"
                        }`}>
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                                // Headers
                                h1: ({node, ...props}) => <h1 className={`text-xl font-bold mb-2 ${message.type === "user" ? "text-white" : "text-gray-900"}`} {...props} />,
                                h2: ({node, ...props}) => <h2 className={`text-lg font-semibold mb-2 ${message.type === "user" ? "text-white" : "text-gray-800"}`} {...props} />,
                                h3: ({node, ...props}) => <h3 className={`text-base font-medium mb-1 ${message.type === "user" ? "text-white" : "text-gray-700"}`} {...props} />,
                                
                                // Paragraphs
                                p: ({node, ...props}) => <p className={`mb-2 ${message.type === "user" ? "text-white" : "text-gray-800"}`} {...props} />,
                                
                                // Lists
                                ul: ({node, ...props}) => <ul className={`list-disc list-inside mb-2 ${message.type === "user" ? "text-white" : "text-gray-800"}`} {...props} />,
                                ol: ({node, ...props}) => <ol className={`list-decimal list-inside mb-2 ${message.type === "user" ? "text-white" : "text-gray-800"}`} {...props} />,
                                li: ({node, ...props}) => <li className={`mb-1 ${message.type === "user" ? "text-white" : "text-gray-800"}`} {...props} />,
                                
                                // Code
                                code: ({node, ...props}: any) => {
                                  const isInline = !props.className?.includes('language-');
                                  return isInline 
                                    ? <code className={`px-1 py-0.5 rounded text-sm font-mono ${
                                        message.type === "user" 
                                          ? "bg-white/20 text-white" 
                                          : "bg-gray-100 text-gray-800"
                                      }`} {...props} />
                                    : <code className={`block p-3 rounded-lg text-sm font-mono overflow-x-auto ${
                                        message.type === "user" 
                                          ? "bg-white/10 text-white" 
                                          : "bg-gray-100 text-gray-800"
                                      }`} {...props} />;
                                },
                                
                                pre: ({node, ...props}) => <pre className="mb-2 overflow-x-auto" {...props} />,
                                
                                // Tables
                                table: ({node, ...props}) => (
                                  <div className="overflow-x-auto mb-4">
                                    <table className="min-w-full divide-y divide-gray-300 border border-gray-200 rounded-lg" {...props} />
                                  </div>
                                ),
                                thead: ({node, ...props}) => <thead className="bg-gray-50" {...props} />,
                                th: ({node, ...props}) => <th scope="col" className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200" {...props} />,
                                tbody: ({node, ...props}) => <tbody className="bg-white divide-y divide-gray-200" {...props} />,
                                tr: ({node, ...props}) => <tr className="hover:bg-gray-50" {...props} />,
                                td: ({node, ...props}) => <td className="px-4 py-2 text-sm text-gray-800 border-b border-gray-100" {...props} />,
                                
                                // Links
                                a: ({node, ...props}) => <a className={`underline hover:no-underline ${
                                  message.type === "user" ? "text-white hover:text-blue-100" : "text-blue-600 hover:text-blue-800"
                                }`} {...props} />,
                                
                                // Blockquotes
                                blockquote: ({node, ...props}) => <blockquote className={`border-l-4 pl-4 italic mb-2 ${
                                  message.type === "user" ? "border-white/30 text-white/90" : "border-gray-300 text-gray-600"
                                }`} {...props} />,
                                
                                // Strong/Bold
                                strong: ({node, ...props}) => <strong className={`font-semibold ${
                                  message.type === "user" ? "text-white" : "text-gray-900"
                                }`} {...props} />,
                                
                                // Emphasis/Italic
                                em: ({node, ...props}) => <em className={`italic ${
                                  message.type === "user" ? "text-white" : "text-gray-800"
                                }`} {...props} />,
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                        <div className={`text-xs mt-2 ${
                          message.type === "user" ? "text-blue-100" : "text-gray-500"
                        }`}>
                          {message.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                  {isTyping && (
                    <div className="flex items-start space-x-4">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-r from-gray-100 to-blue-100 text-gray-700 flex items-center justify-center shadow-md">
                        <Bot className="w-5 h-5" />
                      </div>
                      <div className="bg-white border border-gray-200 p-4 rounded-2xl shadow-md">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>
              
              <div className="flex items-center space-x-3 mt-6 pt-4 border-t border-gray-200">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me about your HR data..."
                  className="flex-1 h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                />
                <Button 
                  onClick={handleSendMessage} 
                  disabled={!input.trim() || isTyping}
                  className="button h-12 px-6 shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  <Send className="w-5 h-5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg font-bold text-gray-800">Quick Questions</CardTitle>
              <CardDescription className="text-sm text-gray-600">Try these sample queries</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {quickQuestions.map((question, index) => (
                <Button
                  key={index}
                  variant="outline"
                  className="w-full text-left justify-start h-auto p-3 text-sm font-medium shadow-sm hover:shadow-md transition-all duration-300 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50"
                  onClick={() => handleQuickQuestion(question)}
                >
                  {question}
                </Button>
              ))}
            </CardContent>
          </Card>

          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg font-bold text-gray-800">Analytics Overview</CardTitle>
              <CardDescription className="text-sm text-gray-600">Key metrics at a glance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
              <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-blue-600" />
                  <span className="text-sm font-medium text-gray-700">Applications</span>
                </div>
                <Badge className="bg-green-100 text-green-800 hover:bg-green-200">+23%</Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
              <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-600" />
                  <span className="text-sm font-medium text-gray-700">Active Jobs</span>
                </div>
                <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">12</Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
              <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-600" />
                  <span className="text-sm font-medium text-gray-700">Conversion Rate</span>
              </div>
                <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-200">16%</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ChatBot;
