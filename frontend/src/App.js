import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import "./App.css";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./components/ui/card";
import { Progress } from "./components/ui/progress";
import { Badge } from "./components/ui/badge";
import { Separator } from "./components/ui/separator";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Input } from "./components/ui/input";
import { Textarea } from "./components/ui/textarea";
import { toast, Toaster } from "sonner";
import { ChevronLeft, ChevronRight, Volume2, MessageCircle, Trophy, Target, BookOpen } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lesson/:letterId" element={<LessonPlayer />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </div>
  );
}

// Home Dashboard Component
const Home = () => {
  const [alphabet, setAlphabet] = useState([]);
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showChat, setShowChat] = useState(false);

  useEffect(() => {
    fetchAlphabet();
    fetchProgress();
  }, []);

  const fetchAlphabet = async () => {
    try {
      const response = await axios.get(`${API}/alphabet`);
      setAlphabet(response.data);
    } catch (error) {
      console.error("Error fetching alphabet:", error);
      toast.error("Failed to load Arabic alphabet");
    }
  };

  const fetchProgress = async () => {
    try {
      const response = await axios.get(`${API}/progress`);
      setProgress(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching progress:", error);
      setLoading(false);
    }
  };

  const getProgressForLetter = (letterId) => {
    return progress.find(p => p.letter_id === letterId);
  };

  const calculateOverallProgress = () => {
    if (!progress.length) return 0;
    const completedLetters = progress.filter(p => p.completed).length;
    return Math.round((completedLetters / 28) * 100);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
          <p className="mt-4 text-emerald-800 font-medium">Loading Arabic lessons...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-emerald-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-emerald-900">Quranic Arabic</h1>
                <p className="text-emerald-700 text-sm">Learn Arabic for the Quran</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm text-emerald-700">Overall Progress</p>
                <div className="flex items-center space-x-2">
                  <Progress value={calculateOverallProgress()} className="w-24" />
                  <span className="text-sm font-semibold text-emerald-800">
                    {calculateOverallProgress()}%
                  </span>
                </div>
              </div>
              <Button 
                onClick={() => setShowChat(true)}
                variant="outline" 
                size="sm"
                className="border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                data-testid="open-chat-button"
              >
                <MessageCircle className="w-4 h-4 mr-2" />
                AI Tutor
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Progress Summary */}
        <Card className="mb-8 border-emerald-200 bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center text-emerald-900">
              <Target className="w-5 h-5 mr-2" />
              Your Learning Journey
            </CardTitle>
            <CardDescription className="text-emerald-700">
              Master the Arabic alphabet to unlock Quranic understanding
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-emerald-600 mb-1">
                  {progress.filter(p => p.completed).length}
                </div>
                <p className="text-sm text-emerald-700">Letters Mastered</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-teal-600 mb-1">
                  {progress.length > 0 ? Math.round(progress.reduce((sum, p) => sum + p.score, 0) / progress.length) : 0}
                </div>
                <p className="text-sm text-emerald-700">Average Score</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-emerald-600 mb-1">
                  {28 - progress.filter(p => p.completed).length}
                </div>
                <p className="text-sm text-emerald-700">Letters Remaining</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Arabic Alphabet Grid */}
        <Card className="border-emerald-200 bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-emerald-900">Arabic Alphabet - الأبجدية العربية</CardTitle>
            <CardDescription className="text-emerald-700">
              Click on any letter to start learning. Each letter includes pronunciation, examples, and practice exercises.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 gap-4">
              {alphabet.map((letter) => {
                const letterProgress = getProgressForLetter(letter.id);
                const isCompleted = letterProgress?.completed || false;
                const score = letterProgress?.score || 0;
                
                return (
                  <Card 
                    key={letter.id}
                    className={`cursor-pointer transition-all duration-200 hover:scale-105 hover:shadow-lg border-2 ${
                      isCompleted 
                        ? 'border-emerald-400 bg-emerald-50' 
                        : 'border-gray-200 hover:border-emerald-300'
                    }`}
                    onClick={() => window.location.href = `/lesson/${letter.id}`}
                    data-testid={`letter-card-${letter.id}`}
                  >
                    <CardContent className="p-4 text-center">
                      <div className="text-4xl font-bold mb-2 text-emerald-900 arabic-text">
                        {letter.arabic}
                      </div>
                      <div className="text-sm font-semibold text-emerald-800 mb-1">
                        {letter.name}
                      </div>
                      <div className="text-xs text-emerald-600 mb-2">
                        {letter.transliteration}
                      </div>
                      
                      {isCompleted && (
                        <div className="flex items-center justify-center space-x-1">
                          <Trophy className="w-3 h-3 text-yellow-500" />
                          <span className="text-xs text-emerald-700">
                            {score}%
                          </span>
                        </div>
                      )}
                      
                      {!isCompleted && letterProgress && (
                        <Badge variant="outline" className="text-xs border-emerald-300 text-emerald-700">
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

      {/* AI Chat Dialog */}
      <AITutorChat open={showChat} onClose={() => setShowChat(false)} />
    </div>
  );
};

// Lesson Player Component
const LessonPlayer = () => {
  const [letter, setLetter] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);
  
  const letterId = parseInt(window.location.pathname.split('/')[2]);

  useEffect(() => {
    fetchLetter();
  }, [letterId]);

  const fetchLetter = async () => {
    try {
      const response = await axios.get(`${API}/alphabet/${letterId}`);
      setLetter(response.data);
    } catch (error) {
      console.error("Error fetching letter:", error);
      toast.error("Failed to load letter");
    }
  };

  const playPronunciation = async (text, type = "letter") => {
    if (isPlaying) return;
    
    setIsPlaying(true);
    try {
      const response = await axios.post(`${API}/tts/generate`, {
        text: text,
        voice_id: "21m00Tcm4TlvDq8ikWAM"
      });
      
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      }
      
      const audio = new Audio(response.data.audio_url);
      setCurrentAudio(audio);
      
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => {
        setIsPlaying(false);
        toast.error("Error playing audio");
      };
      
      await audio.play();
      toast.success(`Playing ${type} pronunciation`);
      
    } catch (error) {
      console.error("Error playing pronunciation:", error);
      setIsPlaying(false);
      toast.error("Failed to play pronunciation");
    }
  };

  const markAsCompleted = async () => {
    try {
      await axios.post(`${API}/progress`, {
        letter_id: letterId,
        completed: true,
        score: 100,
        attempts: 1
      });
      toast.success("Letter marked as completed!");
    } catch (error) {
      console.error("Error saving progress:", error);
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
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
          <p className="mt-4 text-emerald-800 font-medium">Loading lesson...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-emerald-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => window.location.href = '/'}
                className="border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                data-testid="back-to-home-button"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Home
              </Button>
              <div>
                <h1 className="text-xl font-bold text-emerald-900">
                  Letter {letter.id}: {letter.name}
                </h1>
                <p className="text-emerald-700 text-sm">Arabic Alphabet Lesson</p>
              </div>
            </div>
            
            <Button 
              onClick={() => setShowChat(true)}
              variant="outline" 
              size="sm"
              className="border-emerald-300 text-emerald-700 hover:bg-emerald-50"
              data-testid="lesson-chat-button"
            >
              <MessageCircle className="w-4 h-4 mr-2" />
              Ask Tutor
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Main Letter Display */}
        <Card className="mb-8 border-emerald-200 bg-white/90 backdrop-blur-sm">
          <CardContent className="p-12 text-center">
            <div className="text-9xl font-bold mb-6 text-emerald-900 arabic-text">
              {letter.arabic}
            </div>
            
            <div className="space-y-4">
              <h2 className="text-3xl font-bold text-emerald-800">{letter.name}</h2>
              <p className="text-xl text-emerald-700">Transliteration: {letter.transliteration}</p>
              
              <div className="flex justify-center space-x-4 mt-6">
                <Button 
                  onClick={() => playPronunciation(letter.pronunciation)}
                  disabled={isPlaying}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                  data-testid="play-letter-pronunciation"
                >
                  <Volume2 className="w-4 h-4 mr-2" />
                  {isPlaying ? "Playing..." : `Play "${letter.name}"`}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Example Word */}
        <Card className="mb-8 border-emerald-200 bg-white/90 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-emerald-900">Example Word</CardTitle>
            <CardDescription className="text-emerald-700">
              Learn this letter in context with a real Arabic word
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <div className="text-2xl font-bold text-emerald-900 mb-4 arabic-text">
              {letter.example_word.split(' (')[0]}
            </div>
            <p className="text-lg text-emerald-700 mb-4">
              {letter.example_word.split('(')[1]?.replace(')', '')}
            </p>
            <Button 
              onClick={() => playPronunciation(letter.example_word.split(' (')[0], "example word")}
              disabled={isPlaying}
              variant="outline"
              className="border-emerald-300 text-emerald-700 hover:bg-emerald-50"
              data-testid="play-example-word"
            >
              <Volume2 className="w-4 h-4 mr-2" />
              Play Example
            </Button>
          </CardContent>
        </Card>

        {/* Navigation and Completion */}
        <div className="flex justify-between items-center">
          <Button 
            onClick={() => navigateToLetter('prev')}
            disabled={letterId === 1}
            variant="outline"
            className="border-emerald-300 text-emerald-700 hover:bg-emerald-50"
            data-testid="previous-letter-button"
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Previous Letter
          </Button>
          
          <Button 
            onClick={markAsCompleted}
            className="bg-emerald-600 hover:bg-emerald-700 text-white"
            data-testid="mark-completed-button"
          >
            <Trophy className="w-4 h-4 mr-2" />
            Mark as Completed
          </Button>
          
          <Button 
            onClick={() => navigateToLetter('next')}
            disabled={letterId === 28}
            variant="outline"
            className="border-emerald-300 text-emerald-700 hover:bg-emerald-50"
            data-testid="next-letter-button"
          >
            Next Letter
            <ChevronRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </div>

      {/* AI Chat Dialog */}
      <AITutorChat 
        open={showChat} 
        onClose={() => setShowChat(false)}
        context={`Current lesson: Arabic letter ${letter.name} (${letter.arabic})`}
      />
    </div>
  );
};

// AI Tutor Chat Component
const AITutorChat = ({ open, onClose, context }) => {
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
      const response = await axios.post(`${API}/chat`, {
        message: userMessage,
        context: context
      });
      
      // Add AI response to chat
      setChatHistory(prev => [...prev, { type: 'ai', content: response.data.response }]);
      
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

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-emerald-900">AI Arabic Tutor</DialogTitle>
          <DialogDescription className="text-emerald-700">
            Ask questions about Arabic letters, pronunciation, or Islamic context
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex-1 overflow-y-auto space-y-4 py-4">
          {chatHistory.length === 0 && (
            <div className="text-center text-emerald-600 py-8">
              <MessageCircle className="w-12 h-12 mx-auto mb-4 text-emerald-400" />
              <p>Start a conversation with your AI Arabic tutor!</p>
              <p className="text-sm mt-2">Try asking: "How do I pronounce the letter ب?"</p>
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
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-3">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-75"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-150"></div>
                </div>
              </div>
            </div>
          )}
        </div>
        
        <Separator />
        
        <div className="flex space-x-2 pt-4">
          <Textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about Arabic letters, pronunciation, or Islamic context..."
            className="flex-1 min-h-[40px] max-h-[120px] resize-none"
            data-testid="chat-input"
          />
          <Button 
            onClick={sendMessage}
            disabled={!message.trim() || isLoading}
            className="bg-emerald-600 hover:bg-emerald-700"
            data-testid="send-message-button"
          >
            Send
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default App;