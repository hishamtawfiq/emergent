import React, { useState, useEffect } from "react";
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
  X
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth context
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

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      setToken(null);
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = (token, user) => {
    localStorage.setItem('token', token);
    setToken(token);
    setUser(user);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
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

// Landing Page with Auth
const LandingPage = () => {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Quranic Arabic</h1>
                <p className="text-slate-600 text-sm">Learn Arabic for the Quran</p>
              </div>
            </div>
            
            <div className="flex space-x-3">
              <Button 
                onClick={() => setShowLogin(true)}
                variant="outline"
                className="border-blue-300 text-blue-700 hover:bg-blue-50"
                data-testid="login-button"
              >
                Login
              </Button>
              <Button 
                onClick={() => setShowRegister(true)}
                className="bg-blue-600 hover:bg-blue-700"
                data-testid="register-button"
              >
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <div className="max-w-6xl mx-auto px-6 py-20 text-center">
        <h2 className="text-5xl font-bold text-slate-900 mb-6">
          Master Arabic for the Quran
        </h2>
        <p className="text-xl text-slate-600 mb-12 max-w-2xl mx-auto">
          Learn the Arabic alphabet with interactive lessons, pronunciation practice, 
          and gamified progress tracking designed for English-speaking Muslims.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
          <Card className="border-slate-200 bg-white/80">
            <CardHeader className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-xl mx-auto mb-4 flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-blue-600" />
              </div>
              <CardTitle className="text-slate-900">28 Arabic Letters</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">
                Complete interactive lessons for each letter of the Arabic alphabet 
                with proper pronunciation and examples.
              </p>
            </CardContent>
          </Card>
          
          <Card className="border-slate-200 bg-white/80">
            <CardHeader className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-xl mx-auto mb-4 flex items-center justify-center">
                <Volume2 className="w-6 h-6 text-green-600" />
              </div>
              <CardTitle className="text-slate-900">Audio Practice</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">
                Listen to native Arabic pronunciation and practice with 
                high-quality text-to-speech technology.
              </p>
            </CardContent>
          </Card>
          
          <Card className="border-slate-200 bg-white/80">
            <CardHeader className="text-center">
              <div className="w-12 h-12 bg-yellow-100 rounded-xl mx-auto mb-4 flex items-center justify-center">
                <Trophy className="w-6 h-6 text-yellow-600" />
              </div>
              <CardTitle className="text-slate-900">Progress Tracking</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">
                Earn XP, unlock achievements, and track your progress 
                through gamified learning experiences.
              </p>
            </CardContent>
          </Card>
        </div>
        
        <Button 
          onClick={() => setShowRegister(true)}
          size="lg"
          className="mt-12 bg-blue-600 hover:bg-blue-700 text-lg px-8 py-6"
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

// Login Dialog
const LoginDialog = ({ open, onClose }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      login(response.data.access_token, response.data.user);
      toast.success("Welcome back!");
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
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
            className="w-full" 
            disabled={loading}
            data-testid="login-submit"
          >
            {loading ? "Signing in..." : "Sign In"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// Register Dialog
const RegisterDialog = ({ open, onClose }) => {
  const { login } = useAuth();
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
      login(response.data.access_token, response.data.user);
      toast.success("Account created successfully!");
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
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
            className="w-full" 
            disabled={loading}
            data-testid="register-submit"
          >
            {loading ? "Creating Account..." : "Create Account"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [lessons, setLessons] = useState([]);
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);

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
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Arabic Learning</h1>
                <p className="text-slate-600 text-sm">Welcome back, {user?.full_name}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm text-slate-600">Progress</p>
                <div className="flex items-center space-x-2">
                  <Progress value={calculateOverallProgress()} className="w-24" />
                  <span className="text-sm font-semibold text-slate-700">
                    {calculateOverallProgress()}%
                  </span>
                </div>
              </div>
              
              <div className="text-center">
                <p className="text-sm text-slate-600">Level</p>
                <p className="text-lg font-bold text-blue-600">{user?.current_level || 1}</p>
              </div>
              
              <div className="text-center">
                <p className="text-sm text-slate-600">XP</p>
                <p className="text-lg font-bold text-yellow-600">{user?.total_xp || 0}</p>
              </div>
              
              <Button 
                onClick={logout}
                variant="outline" 
                size="sm"
                className="border-slate-300"
                data-testid="logout-button"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Progress Summary */}
        <Card className="mb-8 border-slate-200 bg-white/80">
          <CardHeader>
            <CardTitle className="flex items-center text-slate-900">
              <Trophy className="w-5 h-5 mr-2 text-yellow-500" />
              Your Learning Journey
            </CardTitle>
            <CardDescription>
              Master all 28 Arabic letters to complete the alphabet course
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-1">
                  {progress.filter(p => p.completed).length}
                </div>
                <p className="text-sm text-slate-600">Letters Mastered</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 mb-1">
                  {progress.length > 0 ? Math.round(progress.reduce((sum, p) => sum + p.score, 0) / progress.length) : 0}%
                </div>
                <p className="text-sm text-slate-600">Average Score</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-600 mb-1">
                  {user?.total_xp || 0}
                </div>
                <p className="text-sm text-slate-600">Total XP</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 mb-1">
                  {28 - progress.filter(p => p.completed).length}
                </div>
                <p className="text-sm text-slate-600">Remaining</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Arabic Alphabet Grid */}
        <Card className="border-slate-200 bg-white/80">
          <CardHeader>
            <CardTitle className="text-slate-900">Arabic Alphabet - الأبجدية العربية</CardTitle>
            <CardDescription>
              Complete lessons unlock sequentially. Click on available letters to start learning.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 gap-4">
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
                    <CardContent className="p-4 text-center">
                      <div className="text-4xl font-bold mb-2 text-slate-900 arabic-text">
                        {letter.arabic}
                      </div>
                      <div className="text-sm font-semibold text-slate-800 mb-1">
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
    </div>
  );
};

// Lesson Player Component
const LessonPlayer = () => {
  const [letter, setLetter] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);
  
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
      toast.success(`Playing ${type}`);
      
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

  if (!letter) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => window.location.href = '/'}
                data-testid="back-to-home"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Dashboard
              </Button>
              <div>
                <h1 className="text-xl font-bold text-slate-900">
                  Lesson {letter.id}: {letter.name}
                </h1>
                <p className="text-slate-600 text-sm">{letter.arabic} - {letter.transliteration}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Main Letter Display */}
        <Card className="mb-8 border-slate-200 bg-white/90">
          <CardContent className="p-12 text-center">
            <div className="text-8xl font-bold mb-6 text-slate-900 arabic-text">
              {letter.arabic}
            </div>
            
            <div className="space-y-4">
              <h2 className="text-3xl font-bold text-slate-800">{letter.name}</h2>
              <p className="text-xl text-slate-600">"{letter.transliteration}"</p>
              
              <Button 
                onClick={() => playAudio(letter.pronunciation)}
                disabled={isPlaying}
                className="bg-blue-600 hover:bg-blue-700"
                data-testid="play-pronunciation"
              >
                <Volume2 className="w-4 h-4 mr-2" />
                {isPlaying ? "Playing..." : "Play Pronunciation"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Example Word */}
        <Card className="mb-8 border-slate-200 bg-white/90">
          <CardHeader>
            <CardTitle>Example Word</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <div className="text-3xl font-bold text-slate-900 mb-2 arabic-text">
              {letter.example_word}
            </div>
            <p className="text-lg text-slate-600 mb-4">{letter.example_meaning}</p>
            <Button 
              onClick={() => playAudio(letter.example_word)}
              disabled={isPlaying}
              variant="outline"
              data-testid="play-example"
            >
              <Play className="w-4 h-4 mr-2" />
              Play Example
            </Button>
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <Button 
            onClick={() => navigateToLetter('prev')}
            disabled={letterId === 1}
            variant="outline"
            data-testid="prev-letter"
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>
          
          <Button 
            onClick={markAsCompleted}
            className="bg-green-600 hover:bg-green-700"
            data-testid="complete-lesson"
          >
            <Check className="w-4 h-4 mr-2" />
            Complete Lesson
          </Button>
          
          <Button 
            onClick={() => navigateToLetter('next')}
            disabled={letterId === 28}
            variant="outline"
            data-testid="next-letter"
          >
            Next
            <ChevronRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </div>
    </div>
  );
};

// Quiz Component
const QuizPage = () => {
  const [letter, setLetter] = useState(null);
  const [options, setOptions] = useState([]);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [result, setResult] = useState(null);
  
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
      
    } catch (error) {
      toast.error("Failed to submit answer");
    }
  };

  const nextAction = () => {
    if (letterId < 28) {
      window.location.href = `/lesson/${letterId + 1}`;
    } else {
      window.location.href = '/';
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
      <div className="max-w-2xl mx-auto px-6 py-16">
        {!showResult ? (
          <Card className="border-slate-200 bg-white/90">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Quiz Time!</CardTitle>
              <CardDescription>
                Which letter makes the sound "{letter.pronunciation}"?
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 mb-8">
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
                    <CardContent className="p-8 text-center">
                      <div className="text-6xl font-bold arabic-text">
                        {option.arabic}
                      </div>
                      <p className="text-sm text-slate-600 mt-2">
                        {option.name}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
              
              <Button
                onClick={submitAnswer}
                disabled={!selectedAnswer}
                className="w-full bg-blue-600 hover:bg-blue-700"
                data-testid="submit-quiz"
              >
                Submit Answer
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Card className="border-slate-200 bg-white/90">
            <CardContent className="p-12 text-center">
              <div className={`w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center ${
                result.correct ? 'bg-green-100' : 'bg-red-100'
              }`}>
                {result.correct ? 
                  <Check className="w-10 h-10 text-green-600" /> :
                  <X className="w-10 h-10 text-red-600" />
                }
              </div>
              
              <h2 className="text-2xl font-bold mb-4">
                {result.correct ? "Correct!" : "Try Again!"}
              </h2>
              <p className="text-slate-600 mb-6">{result.message}</p>
              <p className="text-lg font-semibold text-yellow-600 mb-8">
                +{result.xp_earned} XP
              </p>
              
              <Button
                onClick={nextAction}
                className="bg-blue-600 hover:bg-blue-700"
                data-testid="quiz-continue"
              >
                {letterId < 28 ? "Next Letter" : "Complete Course"}
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default App;