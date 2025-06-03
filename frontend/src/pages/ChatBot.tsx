import { useState } from "react";
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
    {
      id: 1,
      type: "bot",
      content: "Hello! I'm your HR AI Assistant. I can help you with analytics, candidate insights, job performance data, and recruitment trends. What would you like to know?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const quickQuestions = [
    "Show me this month's application trends",
    "Which jobs have the highest conversion rates?",
    "What are the top candidate drop-off points?",
    "Compare interview success rates by position",
  ];

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      type: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    // Simulate AI response delay
    setTimeout(() => {
      const botResponse = generateBotResponse(input);
      const botMessage: Message = {
        id: messages.length + 2,
        type: "bot",
        content: botResponse,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, botMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const generateBotResponse = (userInput: string): string => {
    const lowerInput = userInput.toLowerCase();
    
    if (lowerInput.includes("application") || lowerInput.includes("trend")) {
      return "Based on your recent data, applications have increased by 23% this month. The highest activity is for Frontend Developer positions (45 applications) followed by Product Manager roles (32 applications). Would you like me to break this down by week or source?";
    }
    
    if (lowerInput.includes("conversion") || lowerInput.includes("rate")) {
      return "Your top performing jobs by conversion rate are:\n\n1. UX Designer: 18% (5 hired from 28 applications)\n2. Frontend Developer: 16% (8 hired from 45 applications)\n3. Product Manager: 12% (4 hired from 32 applications)\n\nThe average time from application to hire is 18 days. Would you like strategies to improve these rates?";
    }
    
    if (lowerInput.includes("drop") || lowerInput.includes("abandon")) {
      return "The main candidate drop-off points are:\n\n• Experience section: 35% drop-off\n• Portfolio upload: 25% drop-off\n• Cover letter: 20% drop-off\n\nI recommend making the portfolio upload optional initially and adding a progress indicator to reduce abandonment. Should I provide more specific recommendations?";
    }
    
    if (lowerInput.includes("interview")) {
      return "Interview success rates by position:\n\n• UX Designer: 75% (9 successful from 12 interviews)\n• Backend Engineer: 67% (6 successful from 9 interviews)\n• Product Manager: 60% (6 successful from 10 interviews)\n\nThe average interview-to-hire time is 12 days. Would you like me to analyze interviewer performance or suggest interview optimizations?";
    }
    
    if (lowerInput.includes("candidate") || lowerInput.includes("profile")) {
      return "Your candidate pool shows strong diversity in experience levels. Top candidate sources are:\n\n• LinkedIn: 40%\n• Direct applications: 25%\n• Referrals: 20%\n• Job boards: 15%\n\nCandidates with 3-5 years experience have the highest success rate (72%). Need insights on any specific candidate segment?";
    }
    
    return "I understand you're asking about HR data and insights. While I'm still learning about your specific metrics, I can help you analyze trends, compare performance across jobs, and identify optimization opportunities. Could you be more specific about what data you'd like me to examine?";
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
                        <div className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</div>
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
