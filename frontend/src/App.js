import React, { useState, useEffect, useRef } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import "./App.css";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Progress } from "./components/ui/progress";
import { Badge } from "./components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./components/ui/dialog";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { ScrollArea } from "./components/ui/scroll-area";
import { toast, Toaster } from "sonner";
import { 
  ChevronLeft, 
  ChevronRight, 
  Volume2, 
  Trophy, 
  Star, 
  BookOpen, 
  User,
  LogOut,
  Play,
  Check,
  X,
  RotateCcw,
  AlertTriangle,
  MessageCircle,
  Mic,
  Send,
  Bot,
  Lightbulb,
  MicOff
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth context (unchanged from previous implementation)
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refresh_token'));

  useEffect(() => {
    // Check for Google OAuth session_id in URL fragment first
    const urlFragment = window.location.hash.substring(1);
    const params = new URLSearchParams(urlFragment);
    const sessionId = params.get('session_id');
    
    if (sessionId) {
      processGoogleAuth(sessionId);
      return;
    }
    
    // Check existing session
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      checkExistingSession();
    }
  }, [token]);

  const processGoogleAuth = async (sessionId) => {
    try {
      setLoading(true);
      
      const response = await axios.post(`${API}/auth/session`, {}, {
        headers: { "X-Session-ID": sessionId }
      });
      
      setUser(response.data.user);
      
      // Clean URL fragment
      window.history.replaceState(null, null, window.location.pathname);
      
      toast.success("Successfully logged in with Google!");
      
    } catch (error) {
      console.error("Google auth error:", error);
      toast.error("Google authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const checkExistingSession = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      // No existing session
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      
      // Schedule token refresh
      scheduleTokenRefresh();
      
    } catch (error) {
      if (error.response?.status === 401 && refreshToken) {
        await attemptTokenRefresh();
      } else {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const scheduleTokenRefresh = () => {
    // Refresh token 5 minutes before expiry
    const refreshTime = 6.9 * 24 * 60 * 60 * 1000; // 6.9 days in ms
    setTimeout(attemptTokenRefresh, refreshTime);
  };

  const attemptTokenRefresh = async () => {
    if (!refreshToken) {
      logout();
      return;
    }

    try {
      const response = await axios.post(`${API}/auth/refresh`, {
        refresh_token: refreshToken
      });
      
      login(response.data.access_token, response.data.user, response.data.refresh_token);
      
    } catch (error) {
      console.error("Token refresh failed:", error);
      logout();
    }
  };

  const login = (accessToken, userData, newRefreshToken) => {
    localStorage.setItem('token', accessToken);
    localStorage.setItem('refresh_token', newRefreshToken);
    setToken(accessToken);
    setRefreshToken(newRefreshToken);
    setUser(userData);
    axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
    
    scheduleTokenRefresh();
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (error) {
      // Logout on frontend even if backend fails
    }
    
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setRefreshToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  const loginWithGoogle = () => {
    const redirectUrl = encodeURIComponent(window.location.origin);
    window.location.href = `https://auth.emergentagent.com/?redirect=${redirectUrl}`;
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loginWithGoogle, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
        <Toaster position="top-right" />
      </div>
    </AuthProvider>
  );
}

const AppRoutes = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route 
        path="/" 
        element={user ? <Dashboard /> : <LandingPage />} 
      />
      <Route 
        path="/lesson/:letterId" 
        element={user ? <LessonPlayer /> : <Navigate to="/" />} 
      />
      <Route 
        path="/quiz/:letterId" 
        element={user ? <QuizPage /> : <Navigate to="/" />} 
      />
    </Routes>
  );
};

// Landing Page with Auth (unchanged from previous implementation)
const LandingPage = () => {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Mobile-optimized Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
                <BookOpen className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg sm:text-2xl font-bold text-slate-900">Quranic Arabic</h1>
                <p className="text-xs sm:text-sm text-slate-600 hidden sm:block">Learn Arabic for the Quran</p>
              </div>
            </div>
            
            <div className="flex space-x-2 sm:space-x-3">
              <Button 
                onClick={() => setShowLogin(true)}
                variant="outline"
                size="sm"
                className="border-blue-300 text-blue-700 hover:bg-blue-50 text-xs sm:text-sm px-2 sm:px-4 min-h-[44px]"
                data-testid="login-button"
              >
                Login
              </Button>
              <Button 
                onClick={() => setShowRegister(true)}
                size="sm"
                className="bg-blue-600 hover:bg-blue-700 text-xs sm:text-sm px-2 sm:px-4 min-h-[44px]"
                data-testid="register-button"
              >
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Hero Section - Mobile Optimized */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-20 text-center">
        <h2 className="text-3xl sm:text-5xl font-bold text-slate-900 mb-4 sm:mb-6 leading-tight">
          Master Arabic for the Quran
        </h2>
        <p className="text-base sm:text-xl text-slate-600 mb-8 sm:mb-12 max-w-2xl mx-auto px-4">
          Learn the Arabic alphabet with AI tutoring, interactive lessons, pronunciation practice, 
          and gamified progress tracking designed for English-speaking Muslims.
        </p>
        
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8 mt-12 sm:mt-16 px-4">
          <Card className="border-slate-200 bg-white/80">
            <CardHeader className="text-center pb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-blue-100 rounded-xl mx-auto mb-3 sm:mb-4 flex items-center justify-center">
                <BookOpen className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" />
              </div>
              <CardTitle className="text-slate-900 text-lg sm:text-xl">28 Arabic Letters</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600 text-sm sm:text-base">
                Complete interactive lessons for each letter of the Arabic alphabet 
                with proper pronunciation and examples.
              </p>
            </CardContent>
          </Card>
          
          <Card className="border-slate-200 bg-white/80">
            <CardHeader className="text-center pb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-green-100 rounded-xl mx-auto mb-3 sm:mb-4 flex items-center justify-center">
                <Bot className="w-5 h-5 sm:w-6 sm:h-6 text-green-600" />
              </div>
              <CardTitle className="text-slate-900 text-lg sm:text-xl">AI Tutor</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600 text-sm sm:text-base">
                Get personalized help from Ustaz Ahmed, your AI Arabic tutor with 
                Islamic context and pronunciation guidance.
              </p>
            </CardContent>
          </Card>
          
          <Card className="border-slate-200 bg-white/80">
            <CardHeader className="text-center pb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-yellow-100 rounded-xl mx-auto mb-3 sm:mb-4 flex items-center justify-center">
                <Trophy className="w-5 h-5 sm:w-6 sm:h-6 text-yellow-600" />
              </div>
              <CardTitle className="text-slate-900 text-lg sm:text-xl">Progress Tracking</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600 text-sm sm:text-base">
                Earn XP, unlock achievements, and track your progress 
                through gamified learning experiences.
              </p>
            </CardContent>
          </Card>
        </div>
        
        <Button 
          onClick={() => setShowRegister(true)}
          size="lg"
          className="mt-8 sm:mt-12 bg-blue-600 hover:bg-blue-700 text-base sm:text-lg px-6 sm:px-8 py-3 sm:py-6 min-h-[44px]"
          data-testid="hero-get-started-button"
        >
          Start Learning Arabic
        </Button>
      </div>

      {/* Auth Dialogs */}
      <LoginDialog open={showLogin} onClose={() => setShowLogin(false)} />
      <RegisterDialog open={showRegister} onClose={() => setShowRegister(false)} />
    </div>
  );
};

// Login Dialog with Google OAuth
const LoginDialog = ({ open, onClose }) => {
  const { login, loginWithGoogle } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      login(response.data.access_token, response.data.user, response.data.refresh_token);
      toast.success("Welcome back!");
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    onClose();
    loginWithGoogle();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Login to Your Account</DialogTitle>
          <DialogDescription>
            Enter your credentials to continue learning Arabic
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Google OAuth Button */}
          <Button
            onClick={handleGoogleLogin}
            variant="outline"
            className="w-full min-h-[44px]"
            data-testid="google-login-button"
          >
            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </Button>
          
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or</span>
            </div>
          </div>

          {/* Email/Password Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                data-testid="login-email"
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                data-testid="login-password"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full min-h-[44px]" 
              disabled={loading}
              data-testid="login-submit"
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Register Dialog with Google OAuth
const RegisterDialog = ({ open, onClose }) => {
  const { login, loginWithGoogle } = useAuth();
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: ""
  });
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/auth/register`, formData);
      login(response.data.access_token, response.data.user, response.data.refresh_token);
      toast.success("Account created successfully!");
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleRegister = () => {
    onClose();
    loginWithGoogle();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create Your Account</DialogTitle>
          <DialogDescription>
            Join thousands learning Arabic for the Quran
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Google OAuth Button */}
          <Button
            onClick={handleGoogleRegister}
            variant="outline"
            className="w-full min-h-[44px]"
            data-testid="google-register-button"
          >
            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </Button>
          
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or</span>
            </div>
          </div>

          {/* Registration Form */}
          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                required
                data-testid="register-name"
              />
            </div>
            <div>
              <Label htmlFor="reg_email">Email</Label>
              <Input
                id="reg_email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
                data-testid="register-email"
              />
            </div>
            <div>
              <Label htmlFor="reg_password">Password</Label>
              <Input
                id="reg_password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
                data-testid="register-password"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full min-h-[44px]" 
              disabled={loading}
              data-testid="register-submit"
            >
              {loading ? "Creating Account..." : "Create Account"}
            </Button>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// AI Tutor Chat Component
const AITutorChat = ({ open, onClose, lessonId, currentLetter }) => {
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);

  const sendMessage = async () => {
    if (!message.trim() || isLoading) return;
    
    const userMessage = message.trim();
    setMessage("");
    setIsLoading(true);
    
    // Add user message to chat
    setChatHistory(prev => [...prev, { type: 'user', content: userMessage }]);
    
    try {
      const response = await axios.post(`${API}/ai-tutor`, {
        message: userMessage,
        lesson_id: lessonId,
        context_type: "lesson"
      });
      
      // Add AI response to chat
      setChatHistory(prev => [...prev, { 
        type: 'ai', 
        content: response.data.response,
        suggestions: response.data.suggestions || [],
        recommendations: response.data.lesson_recommendations || []
      }]);
      
    } catch (error) {
      console.error("Error sending message:", error);
      setChatHistory(prev => [...prev, { 
        type: 'error', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
      toast.error("Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setMessage(suggestion);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center text-emerald-900">
            <Bot className="w-5 h-5 mr-2" />
            Ustaz Ahmed - AI Arabic Tutor
          </DialogTitle>
          <DialogDescription className="text-emerald-700">
            {currentLetter ? 
              `Get help with letter ${currentLetter.name} (${currentLetter.arabic}) and Islamic context` :
              "Ask questions about Arabic letters, pronunciation, or Islamic context"
            }
          </DialogDescription>
        </DialogHeader>
        
        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-4 py-4">
            {chatHistory.length === 0 && (
              <div className="text-center text-emerald-600 py-8">
                <Bot className="w-12 h-12 mx-auto mb-4 text-emerald-400" />
                <p className="mb-2">Assalamu alaykum! I'm Ustaz Ahmed, your Arabic tutor.</p>
                {currentLetter ? (
                  <div className="space-y-2">
                    <p className="text-sm">Let's learn about letter {currentLetter.name} ({currentLetter.arabic})</p>
                    <div className="flex flex-wrap gap-2 justify-center">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSuggestionClick(`What is the Quranic example for ${currentLetter.name}?`)}
                        className="text-xs"
                      >
                        Quranic examples
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSuggestionClick(`How do I pronounce ${currentLetter.arabic}?`)}
                        className="text-xs"
                      >
                        Pronunciation help
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm mt-2">Ask me anything about Arabic letters or Islamic context!</p>
                )}
              </div>
            )}
            
            {chatHistory.map((msg, index) => (
              <div key={index} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-lg p-3 ${
                  msg.type === 'user' 
                    ? 'bg-emerald-600 text-white' 
                    : msg.type === 'error'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  
                  {/* Show suggestions if available */}
                  {msg.suggestions && msg.suggestions.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <p className="text-xs font-semibold flex items-center">
                        <Lightbulb className="w-3 h-3 mr-1" />
                        Suggestions:
                      </p>
                      {msg.suggestions.map((suggestion, idx) => (
                        <Button
                          key={idx}
                          variant="outline"
                          size="sm"
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="text-xs mr-2 mb-2"
                        >
                          {suggestion}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex items-center space-x-1">
                    <Bot className="w-4 h-4 text-emerald-600" />
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-75"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-150"></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
        
        <div className="flex space-x-2 pt-4 border-t">
          <Textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about Arabic letters, pronunciation, or Islamic context..."
            className="flex-1 min-h-[40px] max-h-[120px] resize-none"
            data-testid="ai-chat-input"
          />
          <Button 
            onClick={sendMessage}
            disabled={!message.trim() || isLoading}
            className="bg-emerald-600 hover:bg-emerald-700 min-h-[44px]"
            data-testid="send-ai-message"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Voice Recording Component
const VoiceRecorder = ({ targetWord, lessonId, onFeedback }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];
      
      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.current.push(event.data);
      };
      
      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        await sendAudioForFeedback(audioBlob);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.current.start();
      setIsRecording(true);
      toast.success("Recording started - say the word clearly!");
      
    } catch (error) {
      console.error("Error accessing microphone:", error);
      toast.error("Could not access microphone");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const sendAudioForFeedback = async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.wav');
      formData.append('target_word', targetWord);
      if (lessonId) {
        formData.append('lesson_id', lessonId.toString());
      }
      
      const response = await axios.post(`${API}/ai-tutor/voice-feedback`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      onFeedback(response.data);
      
    } catch (error) {
      console.error("Error processing audio:", error);
      toast.error("Voice analysis failed - please try again");
      onFeedback({
        transcription: "",
        target_word: targetWord,
        match: false,
        confidence: 0,
        feedback: "Voice analysis temporarily unavailable. Practice by listening to the audio.",
        pronunciation_tips: ["Listen to the audio example", "Practice slowly", "Try again later"]
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col items-center space-y-3">
      <Button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
        variant={isRecording ? "destructive" : "outline"}
        className={`min-h-[44px] ${isRecording ? 'animate-pulse' : ''}`}
        data-testid="voice-recorder-button"
      >
        {isProcessing ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            Analyzing...
          </>
        ) : isRecording ? (
          <>
            <MicOff className="w-4 h-4 mr-2" />
            Stop Recording
          </>
        ) : (
          <>
            <Mic className="w-4 h-4 mr-2" />
            Record Pronunciation
          </>
        )}
      </Button>
      
      {isRecording && (
        <p className="text-sm text-emerald-600 animate-pulse">
          🔴 Recording... Say "{targetWord}" clearly
        </p>
      )}
    </div>
  );
};

// Dashboard Component - Mobile Optimized (unchanged from previous)
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [lessons, setLessons] = useState([]);
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAITutor, setShowAITutor] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [lessonsRes, progressRes] = await Promise.all([
        axios.get(`${API}/lessons`),
        axios.get(`${API}/progress`)
      ]);
      setLessons(lessonsRes.data);
      setProgress(progressRes.data);
    } catch (error) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const getProgressForLetter = (letterId) => {
    return progress.find(p => p.letter_id === letterId);
  };

  const calculateOverallProgress = () => {
    return Math.round((progress.filter(p => p.completed).length / 28) * 100);
  };

  const canAccessLetter = (letterId) => {
    if (letterId === 1) return true;
    const prevLetterProgress = getProgressForLetter(letterId - 1);
    return prevLetterProgress?.completed || false;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading your progress...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Mobile-Optimized Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center flex-shrink-0">
                <BookOpen className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
              </div>
              <div className="min-w-0 flex-1">
                <h1 className="text-lg sm:text-2xl font-bold text-slate-900 truncate">Arabic Learning</h1>
                <p className="text-xs sm:text-sm text-slate-600 truncate">Welcome back, {user?.full_name}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2 sm:space-x-4 flex-shrink-0">
              <Button 
                onClick={() => setShowAITutor(true)}
                variant="outline" 
                size="sm"
                className="border-emerald-300 text-emerald-700 hover:bg-emerald-50 min-h-[44px]"
                data-testid="ai-tutor-button"
              >
                <Bot className="w-4 h-4 mr-1" />
                <span className="hidden sm:inline">AI Tutor</span>
              </Button>
              
              <div className="hidden sm:block text-right">
                <p className="text-sm text-slate-600">Progress</p>
                <div className="flex items-center space-x-2">
                  <Progress value={calculateOverallProgress()} className="w-24" />
                  <span className="text-sm font-semibold text-slate-700">
                    {calculateOverallProgress()}%
                  </span>
                </div>
              </div>
              
              <div className="text-center">
                <p className="text-xs sm:text-sm text-slate-600">Level</p>
                <p className="text-sm sm:text-lg font-bold text-blue-600">{user?.current_level || 1}</p>
              </div>
              
              <div className="text-center">
                <p className="text-xs sm:text-sm text-slate-600">XP</p>
                <p className="text-sm sm:text-lg font-bold text-yellow-600">{user?.total_xp || 0}</p>
              </div>
              
              <Button 
                onClick={logout}
                variant="outline" 
                size="sm"
                className="border-slate-300 p-2 min-h-[44px]"
                data-testid="logout-button"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
          
          {/* Mobile Progress Bar */}
          <div className="sm:hidden mt-3">
            <div className="flex items-center justify-between text-sm text-slate-600 mb-2">
              <span>Overall Progress</span>
              <span className="font-semibold">{calculateOverallProgress()}%</span>
            </div>
            <Progress value={calculateOverallProgress()} className="w-full" />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8 pb-20 sm:pb-8">
        {/* Progress Summary */}
        <Card className="mb-6 sm:mb-8 border-slate-200 bg-white/80">
          <CardHeader>
            <CardTitle className="flex items-center text-slate-900 text-lg sm:text-xl">
              <Trophy className="w-4 h-4 sm:w-5 sm:h-5 mr-2 text-yellow-500" />
              Your Learning Journey
            </CardTitle>
            <CardDescription className="text-sm sm:text-base">
              Master all 28 Arabic letters to complete the alphabet course
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6">
              <div className="text-center">
                <div className="text-2xl sm:text-3xl font-bold text-blue-600 mb-1">
                  {progress.filter(p => p.completed).length}
                </div>
                <p className="text-xs sm:text-sm text-slate-600">Letters Mastered</p>
              </div>
              <div className="text-center">
                <div className="text-2xl sm:text-3xl font-bold text-green-600 mb-1">
                  {progress.length > 0 ? Math.round(progress.reduce((sum, p) => sum + p.score, 0) / progress.length) : 0}%
                </div>
                <p className="text-xs sm:text-sm text-slate-600">Average Score</p>
              </div>
              <div className="text-center">
                <div className="text-2xl sm:text-3xl font-bold text-yellow-600 mb-1">
                  {user?.total_xp || 0}
                </div>
                <p className="text-xs sm:text-sm text-slate-600">Total XP</p>
              </div>
              <div className="text-center">
                <div className="text-2xl sm:text-3xl font-bold text-purple-600 mb-1">
                  {28 - progress.filter(p => p.completed).length}
                </div>
                <p className="text-xs sm:text-sm text-slate-600">Remaining</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Arabic Alphabet Grid */}
        <Card className="border-slate-200 bg-white/80">
          <CardHeader>
            <CardTitle className="text-slate-900 text-lg sm:text-xl">Arabic Alphabet - الأبجدية العربية</CardTitle>
            <CardDescription className="text-sm sm:text-base">
              Complete lessons unlock sequentially. Click on available letters to start learning.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 gap-3 sm:gap-4">
              {lessons.map((letter) => {
                const letterProgress = getProgressForLetter(letter.id);
                const isCompleted = letterProgress?.completed || false;
                const isLocked = !canAccessLetter(letter.id);
                const score = letterProgress?.score || 0;
                
                return (
                  <Card 
                    key={letter.id}
                    className={`cursor-pointer transition-all duration-200 border-2 ${
                      isLocked 
                        ? 'border-gray-200 bg-gray-50 opacity-50 cursor-not-allowed' 
                        : isCompleted 
                        ? 'border-green-400 bg-green-50 hover:shadow-lg hover:scale-105' 
                        : 'border-blue-200 hover:border-blue-400 hover:shadow-lg hover:scale-105'
                    }`}
                    onClick={() => {
                      if (!isLocked) {
                        window.location.href = `/lesson/${letter.id}`;
                      }
                    }}
                    data-testid={`letter-card-${letter.id}`}
                  >
                    <CardContent className="p-3 sm:p-4 text-center">
                      <div className="text-3xl sm:text-4xl font-bold mb-2 text-slate-900 arabic-text">
                        {letter.arabic}
                      </div>
                      <div className="text-xs sm:text-sm font-semibold text-slate-800 mb-1">
                        {letter.name}
                      </div>
                      <div className="text-xs text-slate-600 mb-2">
                        {letter.transliteration}
                      </div>
                      
                      {isCompleted && (
                        <div className="flex items-center justify-center space-x-1">
                          <Trophy className="w-3 h-3 text-yellow-500" />
                          <span className="text-xs text-green-700">
                            {score}%
                          </span>
                        </div>
                      )}
                      
                      {isLocked && (
                        <Badge variant="outline" className="text-xs border-gray-300 text-gray-500">
                          Locked
                        </Badge>
                      )}
                      
                      {!isCompleted && !isLocked && letterProgress && (
                        <Badge variant="outline" className="text-xs border-blue-300 text-blue-700">
                          In Progress
                        </Badge>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Tutor Dialog */}
      <AITutorChat 
        open={showAITutor} 
        onClose={() => setShowAITutor(false)}
        lessonId={null}
        currentLetter={null}
      />
    </div>
  );
};

// Enhanced Lesson Player with AI Tutor and Voice Practice
const LessonPlayer = () => {
  const [letter, setLetter] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);
  const [audioSource, setAudioSource] = useState('');
  const [showAITutor, setShowAITutor] = useState(false);
  const [voiceFeedback, setVoiceFeedback] = useState(null);
  
  const letterId = parseInt(window.location.pathname.split('/')[2]);

  useEffect(() => {
    fetchLetter();
  }, [letterId]);

  const fetchLetter = async () => {
    try {
      const response = await axios.get(`${API}/lessons/${letterId}`);
      setLetter(response.data);
    } catch (error) {
      toast.error("Failed to load lesson");
    }
  };

  const playAudio = async (text, type = "letter") => {
    if (isPlaying) return;
    
    setIsPlaying(true);
    try {
      const response = await axios.post(`${API}/tts/generate`, { text });
      setAudioSource(response.data.source);
      
      if (response.data.source === 'browser') {
        // Use browser speechSynthesis for fallback
        if ('speechSynthesis' in window) {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.lang = 'ar';
          utterance.rate = 0.8;
          utterance.onend = () => setIsPlaying(false);
          utterance.onerror = () => {
            setIsPlaying(false);
            toast.error("Audio playback failed");
          };
          speechSynthesis.speak(utterance);
          toast.success(`Playing ${type} (browser voice)`);
        } else {
          setIsPlaying(false);
          toast.error("Audio not supported on this device");
        }
        return;
      }
      
      // Use provided audio data
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      }
      
      const audio = new Audio(response.data.audio_url);
      setCurrentAudio(audio);
      
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => {
        setIsPlaying(false);
        toast.error("Audio playback failed");
      };
      
      await audio.play();
      
      const sourceText = response.data.source === 'cached' ? ' (cached)' : 
                        response.data.source === 'elevenlabs' ? ' (high quality)' : '';
      toast.success(`Playing ${type}${sourceText}`);
      
    } catch (error) {
      setIsPlaying(false);
      toast.error("Audio generation failed");
    }
  };

  const markAsCompleted = async () => {
    try {
      await axios.post(`${API}/progress`, {
        letter_id: letterId,
        completed: true,
        score: 100,
        attempts: 1,
        xp_earned: 50
      });
      toast.success("Letter completed! +50 XP");
      setTimeout(() => {
        window.location.href = `/quiz/${letterId}`;
      }, 1000);
    } catch (error) {
      toast.error("Failed to save progress");
    }
  };

  const navigateToLetter = (direction) => {
    const newId = direction === 'next' ? letterId + 1 : letterId - 1;
    if (newId >= 1 && newId <= 28) {
      window.location.href = `/lesson/${newId}`;
    }
  };

  const handleVoiceFeedback = (feedback) => {
    setVoiceFeedback(feedback);
    if (feedback.match) {
      toast.success("Great pronunciation! 🎉");
    } else {
      toast.info("Keep practicing! Check the tips below.");
    }
  };

  if (!letter) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Mobile-Optimized Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 sm:space-x-4 min-w-0 flex-1">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => window.location.href = '/'}
                className="flex-shrink-0 min-h-[44px]"
                data-testid="back-to-home"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                <span className="hidden sm:inline">Dashboard</span>
              </Button>
              <div className="min-w-0 flex-1">
                <h1 className="text-lg sm:text-xl font-bold text-slate-900 truncate">
                  Lesson {letter.id}: {letter.name}
                </h1>
                <p className="text-sm text-slate-600 truncate">{letter.arabic} - {letter.transliteration}</p>
              </div>
            </div>
            
            <Button 
              onClick={() => setShowAITutor(true)}
              variant="outline" 
              size="sm"
              className="border-emerald-300 text-emerald-700 hover:bg-emerald-50 min-h-[44px]"
              data-testid="lesson-ai-tutor"
            >
              <Bot className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Ask Tutor</span>
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8 pb-20 sm:pb-8">
        {/* Main Letter Display */}
        <Card className="mb-6 sm:mb-8 border-slate-200 bg-white/90">
          <CardContent className="p-8 sm:p-12 text-center">
            <div className="text-6xl sm:text-8xl font-bold mb-4 sm:mb-6 text-slate-900 arabic-text">
              {letter.arabic}
            </div>
            
            <div className="space-y-3 sm:space-y-4">
              <h2 className="text-2xl sm:text-3xl font-bold text-slate-800">{letter.name}</h2>
              <p className="text-lg sm:text-xl text-slate-600">"{letter.transliteration}"</p>
              
              <Button 
                onClick={() => playAudio(letter.pronunciation)}
                disabled={isPlaying}
                className="bg-blue-600 hover:bg-blue-700 min-h-[44px]"
                data-testid="play-pronunciation"
              >
                <Volume2 className="w-4 h-4 mr-2" />
                {isPlaying ? "Playing..." : "Play Pronunciation"}
              </Button>
              
              {audioSource && (
                <p className="text-sm text-slate-500">
                  Audio source: {audioSource === 'elevenlabs' ? 'High Quality' : 
                               audioSource === 'cached' ? 'Cached' : 'Browser Voice'}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Example Word */}
        <Card className="mb-6 sm:mb-8 border-slate-200 bg-white/90">
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Example Word</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <div className="text-2xl sm:text-3xl font-bold text-slate-900 mb-2 arabic-text">
              {letter.example_word}
            </div>
            <p className="text-base sm:text-lg text-slate-600 mb-4">{letter.example_meaning}</p>
            <Button 
              onClick={() => playAudio(letter.example_word)}
              disabled={isPlaying}
              variant="outline"
              className="min-h-[44px]"
              data-testid="play-example"
            >
              <Play className="w-4 h-4 mr-2" />
              Play Example
            </Button>
          </CardContent>
        </Card>

        {/* Islamic Context */}
        {letter.islamic_context && (
          <Card className="mb-6 sm:mb-8 border-emerald-200 bg-emerald-50">
            <CardHeader>
              <CardTitle className="text-lg sm:text-xl text-emerald-900">Islamic Context</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-emerald-800 mb-4">{letter.islamic_context}</p>
              {letter.quranic_examples && letter.quranic_examples.length > 0 && (
                <div>
                  <p className="font-semibold text-emerald-900 mb-2">Quranic Examples:</p>
                  <div className="space-y-1">
                    {letter.quranic_examples.map((example, idx) => (
                      <p key={idx} className="text-emerald-700 arabic-text text-lg">
                        {example}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Voice Practice Section */}
        <Card className="mb-6 sm:mb-8 border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl text-yellow-900">Voice Practice</CardTitle>
            <CardDescription className="text-yellow-800">
              Practice pronouncing "{letter.name}" and get AI feedback
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <VoiceRecorder 
              targetWord={letter.pronunciation}
              lessonId={letterId}
              onFeedback={handleVoiceFeedback}
            />
            
            {voiceFeedback && (
              <div className="mt-6 p-4 rounded-lg bg-white border">
                <div className="flex items-center justify-center mb-3">
                  {voiceFeedback.match ? (
                    <Check className="w-6 h-6 text-green-600 mr-2" />
                  ) : (
                    <X className="w-6 h-6 text-red-600 mr-2" />
                  )}
                  <p className="font-semibold">
                    {voiceFeedback.match ? "Excellent!" : "Keep Practicing"}
                  </p>
                </div>
                
                <p className="text-sm text-slate-600 mb-3">{voiceFeedback.feedback}</p>
                
                {voiceFeedback.transcription && (
                  <p className="text-sm text-slate-500 mb-3">
                    Heard: "{voiceFeedback.transcription}"
                  </p>
                )}
                
                {voiceFeedback.pronunciation_tips && voiceFeedback.pronunciation_tips.length > 0 && (
                  <div className="text-left">
                    <p className="font-semibold text-sm mb-2">Pronunciation Tips:</p>
                    <ul className="text-sm text-slate-600 space-y-1">
                      {voiceFeedback.pronunciation_tips.map((tip, idx) => (
                        <li key={idx} className="flex items-start">
                          <Lightbulb className="w-3 h-3 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
                          {tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex flex-col sm:flex-row justify-between items-center space-y-3 sm:space-y-0">
          <Button 
            onClick={() => navigateToLetter('prev')}
            disabled={letterId === 1}
            variant="outline"
            className="w-full sm:w-auto min-h-[44px]"
            data-testid="prev-letter"
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>
          
          <Button 
            onClick={markAsCompleted}
            className="bg-green-600 hover:bg-green-700 w-full sm:w-auto min-h-[44px]"
            data-testid="complete-lesson"
          >
            <Check className="w-4 h-4 mr-2" />
            Complete Lesson
          </Button>
          
          <Button 
            onClick={() => navigateToLetter('next')}
            disabled={letterId === 28}
            variant="outline"
            className="w-full sm:w-auto min-h-[44px]"
            data-testid="next-letter"
          >
            Next
            <ChevronRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </div>

      {/* AI Tutor Dialog */}
      <AITutorChat 
        open={showAITutor} 
        onClose={() => setShowAITutor(false)}
        lessonId={letterId}
        currentLetter={letter}
      />
    </div>
  );
};

// Enhanced Quiz with Retry Logic and Score Thresholds (unchanged from previous)
const QuizPage = () => {
  const [letter, setLetter] = useState(null);
  const [options, setOptions] = useState([]);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [result, setResult] = useState(null);
  const [showRetry, setShowRetry] = useState(false);
  
  const letterId = parseInt(window.location.pathname.split('/')[2]);

  useEffect(() => {
    fetchQuizData();
  }, [letterId]);

  const fetchQuizData = async () => {
    try {
      const [letterRes, lessonsRes] = await Promise.all([
        axios.get(`${API}/lessons/${letterId}`),
        axios.get(`${API}/lessons`)
      ]);
      
      setLetter(letterRes.data);
      
      // Generate quiz options (correct answer + 3 random)
      const allLetters = lessonsRes.data;
      const correctLetter = letterRes.data;
      const wrongLetters = allLetters
        .filter(l => l.id !== letterId)
        .sort(() => 0.5 - Math.random())
        .slice(0, 3);
      
      const quizOptions = [correctLetter, ...wrongLetters]
        .sort(() => 0.5 - Math.random());
      
      setOptions(quizOptions);
      
    } catch (error) {
      toast.error("Failed to load quiz");
    }
  };

  const submitAnswer = async () => {
    if (!selectedAnswer) return;
    
    try {
      const response = await axios.post(`${API}/quiz/answer`, {
        letter_id: letterId,
        selected_letter_id: selectedAnswer
      });
      
      setResult(response.data);
      setShowResult(true);
      setShowRetry(!response.data.can_proceed);
      
    } catch (error) {
      toast.error("Failed to submit answer");
    }
  };

  const retryQuiz = () => {
    setSelectedAnswer(null);
    setShowResult(false);
    setShowRetry(false);
    setResult(null);
    // Regenerate options
    fetchQuizData();
  };

  const nextAction = () => {
    if (result.can_proceed) {
      if (letterId < 28) {
        window.location.href = `/lesson/${letterId + 1}`;
      } else {
        window.location.href = '/';
      }
    } else {
      // Review mistakes - go back to lesson
      window.location.href = `/lesson/${letterId}`;
    }
  };

  if (!letter || !options.length) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8 sm:py-16">
        {!showResult ? (
          <Card className="border-slate-200 bg-white/90">
            <CardHeader className="text-center">
              <CardTitle className="text-xl sm:text-2xl">Quiz Time!</CardTitle>
              <CardDescription className="text-sm sm:text-base">
                Which letter makes the sound "{letter.pronunciation}"?
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 sm:gap-4 mb-6 sm:mb-8">
                {options.map((option) => (
                  <Card
                    key={option.id}
                    className={`cursor-pointer transition-all border-2 ${
                      selectedAnswer === option.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                    onClick={() => setSelectedAnswer(option.id)}
                    data-testid={`quiz-option-${option.id}`}
                  >
                    <CardContent className="p-4 sm:p-8 text-center">
                      <div className="text-4xl sm:text-6xl font-bold arabic-text">
                        {option.arabic}
                      </div>
                      <p className="text-xs sm:text-sm text-slate-600 mt-2">
                        {option.name}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
              
              <Button
                onClick={submitAnswer}
                disabled={!selectedAnswer}
                className="w-full bg-blue-600 hover:bg-blue-700 min-h-[44px]"
                data-testid="submit-quiz"
              >
                Submit Answer
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Card className="border-slate-200 bg-white/90">
            <CardContent className="p-8 sm:p-12 text-center">
              <div className={`w-16 h-16 sm:w-20 sm:h-20 rounded-full mx-auto mb-4 sm:mb-6 flex items-center justify-center ${
                result.correct ? 'bg-green-100' : 'bg-red-100'
              }`}>
                {result.correct ? 
                  <Check className="w-8 h-8 sm:w-10 sm:h-10 text-green-600" /> :
                  <X className="w-8 h-8 sm:w-10 sm:h-10 text-red-600" />
                }
              </div>
              
              <h2 className="text-xl sm:text-2xl font-bold mb-4">
                {result.correct ? "Correct!" : "Not Quite Right"}
              </h2>
              <p className="text-slate-600 mb-4 text-sm sm:text-base">{result.message}</p>
              <p className="text-base sm:text-lg font-semibold text-yellow-600 mb-2">
                Score: {result.score}%
              </p>
              {result.xp_earned > 0 && (
                <p className="text-base sm:text-lg font-semibold text-green-600 mb-6">
                  +{result.xp_earned} XP
                </p>
              )}
              
              {!result.can_proceed && (
                <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center justify-center mb-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
                    <span className="text-sm font-semibold text-yellow-800">
                      Need {result.min_score_required}% to proceed
                    </span>
                  </div>
                  <p className="text-sm text-yellow-700">
                    Current score: {result.score}%. Review the lesson or try again!
                  </p>
                </div>
              )}
              
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                {!result.can_proceed && (
                  <>
                    <Button
                      onClick={retryQuiz}
                      variant="outline"
                      className="w-full sm:w-auto min-h-[44px]"
                      data-testid="retry-quiz"
                    >
                      <RotateCcw className="w-4 h-4 mr-2" />
                      Retry Quiz
                    </Button>
                    <Button
                      onClick={nextAction}
                      variant="outline"
                      className="w-full sm:w-auto min-h-[44px]"
                      data-testid="review-lesson"
                    >
                      Review Lesson
                    </Button>
                  </>
                )}
                
                {result.can_proceed && (
                  <Button
                    onClick={nextAction}
                    className="w-full bg-blue-600 hover:bg-blue-700 min-h-[44px]"
                    data-testid="quiz-continue"
                  >
                    {letterId < 28 ? "Next Letter" : "Complete Course"}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default App;