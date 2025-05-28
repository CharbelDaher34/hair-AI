
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
    <div className="flex-1 space-y-6 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-primary" />
            AI Assistant
          </h1>
          <p className="text-muted-foreground">
            Get insights and analytics from your HR data using natural language
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="lg:col-span-3">
          <Card className="h-[600px] flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5" />
                Chat Assistant
              </CardTitle>
              <CardDescription>
                Ask questions about your recruitment data and get AI-powered insights
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <ScrollArea className="flex-1 pr-4">
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex items-start space-x-3 ${
                        message.type === "user" ? "flex-row-reverse space-x-reverse" : ""
                      }`}
                    >
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        message.type === "user" 
                          ? "bg-primary text-primary-foreground" 
                          : "bg-muted"
                      }`}>
                        {message.type === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                      </div>
                      <div className={`max-w-[80%] p-3 rounded-lg ${
                        message.type === "user"
                          ? "bg-primary text-primary-foreground ml-auto"
                          : "bg-muted"
                      }`}>
                        <div className="whitespace-pre-wrap">{message.content}</div>
                        <div className="text-xs opacity-70 mt-1">
                          {message.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                  {isTyping && (
                    <div className="flex items-start space-x-3">
                      <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                        <Bot className="w-4 h-4" />
                      </div>
                      <div className="bg-muted p-3 rounded-lg">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                          <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
              
              <div className="flex items-center space-x-2 mt-4">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me about your HR data..."
                  className="flex-1"
                />
                <Button onClick={handleSendMessage} disabled={!input.trim() || isTyping}>
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Quick Questions</CardTitle>
              <CardDescription>Try these sample queries</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {quickQuestions.map((question, index) => (
                <Button
                  key={index}
                  variant="outline"
                  className="w-full text-left h-auto p-3 justify-start whitespace-normal"
                  onClick={() => handleQuickQuestion(question)}
                >
                  {question}
                </Button>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Data Coverage</CardTitle>
              <CardDescription>What I can help you analyze</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-500" />
                <span className="text-sm">Application trends</span>
                <Badge variant="secondary" className="ml-auto">Active</Badge>
              </div>
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-green-500" />
                <span className="text-sm">Candidate analytics</span>
                <Badge variant="secondary" className="ml-auto">Active</Badge>
              </div>
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-green-500" />
                <span className="text-sm">Job performance</span>
                <Badge variant="secondary" className="ml-auto">Active</Badge>
              </div>
              <div className="flex items-center gap-2">
                <Bot className="h-4 w-4 text-yellow-500" />
                <span className="text-sm">Predictive insights</span>
                <Badge variant="outline" className="ml-auto">Coming Soon</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tips</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p>• Ask specific questions about metrics, trends, or comparisons</p>
              <p>• Request data for specific time periods or job positions</p>
              <p>• Ask for recommendations to improve your processes</p>
              <p>• Use natural language - no need for complex queries</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ChatBot;
