import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Navbar.css';

const Navbar = ({ currentUser, onLogout }) => {
    const navigate = useNavigate();

    const handleLogout = () => {
        onLogout();
        navigate('/login');
    };

    return (
        <nav className="app-nav">
            <div className="nav-container">
                <div className="nav-content">
                    <div className="nav-left">
                        <h1 className="nav-title">
                            Book Management System
                        </h1>
                    </div>
                    <div className="nav-right">
                        <span className="nav-welcome">
                            Welcome, {currentUser.username || currentUser.email}
                        </span>
                        <button
                            onClick={handleLogout}
                            className="nav-logout-button"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;