import React, { useState } from 'react';
import "./Login.css";

const Login = ({ onLogin, onSwitchToRegister }) => {
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
        if (error) setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Basic validation
        if (!formData.username || !formData.password) {
            setError('Please fill in all fields');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await fetch('http://localhost:8000/user/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            const data = await response.json();
            console.log(data);

            if (response.ok) {
                // Store token in localStorage (you might want to use a more secure method)
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                
                // Call the parent's login handler
                onLogin(data.user, data.access_token);
                
                setError('');
            } else {
                setError(data.detail || 'Login failed');
            }
        } catch (err) {
            console.error('Login error:', err);
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-box">
                <div>
                <h2 className="login-title">Sign in to your account</h2>
                <p className="login-subtext">
                    Or{" "}
                    <button onClick={onSwitchToRegister} className="login-switch-btn">
                    create a new account
                    </button>
                </p>
                </div>

                <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    name="username"
                    placeholder="Username"
                    className="login-input"
                    value={formData.username}
                    onChange={handleInputChange}
                />

                <input
                    type="password"
                    name="password"
                    placeholder="Password"
                    className="login-input"
                    value={formData.password}
                    onChange={handleInputChange}
                />

                {error && <div className="login-error">{error}</div>}

                <button type="submit" disabled={loading} className="login-button">
                    {loading ? (
                    <span>
                        <svg
                        className="spinner"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        >
                        <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                        ></circle>
                        <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0..."
                        ></path>
                        </svg>
                        Signing in...
                    </span>
                    ) : (
                    "Sign in"
                    )}
                </button>
                </form>
            </div>
        </div>

    );
};

export default Login;