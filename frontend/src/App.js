import React, { useState, useEffect } from 'react';
import Home from './components/home/Home';
import Login from './components/login/Login';
import Register from './components/register/Register';
// import './index.css';


const App = () => {
    const [currentUser, setCurrentUser] = useState(null);
    const [token, setToken] = useState(null);
    const [currentView, setCurrentView] = useState('login');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const savedToken = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');
        
        if (savedToken && savedUser) {
            try {
                const user = JSON.parse(savedUser);
                console.log(user)
                setToken(savedToken);
                setCurrentUser(user);
                setCurrentView('home');
            } catch (error) {
                console.error('Error parsing saved user data:', error);
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        }
        
        setLoading(false);
    }, []);

    const handleLogin = (user, accessToken) => {
        setCurrentUser(user);
        setToken(accessToken);
        setCurrentView('home');
    };

    const handleRegister = (user) => {
        setCurrentUser(user);
        setCurrentView('login');
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setCurrentUser(null);
        setToken(null);
        setCurrentView('login');
    };

    const switchToRegister = () => {
        setCurrentView('register');
    };

    const switchToLogin = () => {
        setCurrentView('login');
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    // If user is logged in, show the main app
    if (currentUser && currentView === 'home') {
        return (
            <div>
                {/* Navigation bar with logout */}
                <nav className="bg-white shadow-sm border-b">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="flex justify-between h-16">
                            <div className="flex items-center">
                                <h1 className="text-xl font-semibold text-gray-900">
                                    Book Management System
                                </h1>
                            </div>
                            <div className="flex items-center space-x-4">
                                <span className="text-sm text-gray-700">
                                    Welcome, {currentUser.username || currentUser.email}
                                </span>
                                <button
                                    onClick={handleLogout}
                                    className="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                                >
                                    Logout
                                </button>
                            </div>
                        </div>
                    </div>
                </nav>
                
                {/* Pass the user and token to Home component */}
                <Home 
                    currentUser={currentUser} 
                    token={token}
                    isLoggedIn={true}
                />
            </div>
        );
    }

    // Show login or register based on currentView
    if (currentView === 'login') {
        return (
            <Login 
                onLogin={handleLogin}
                onSwitchToRegister={switchToRegister}
            />
        );
    }

    if (currentView === 'register') {
        return (
            <Register 
                onRegister={handleRegister}
                onSwitchToLogin={switchToLogin}
            />
        );
    }

    return null;
};

export default App;
