const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Helper to get token
const getToken = () => {
    if (typeof window !== 'undefined') {
        return localStorage.getItem("access_token");
    }
    return null;
};

// Helper for headers
const getHeaders = (isMultipart = false) => {
    const token = getToken();
    const headers: any = {};

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    if (!isMultipart) {
        headers["Content-Type"] = "application/json";
    }

    return headers;
};

export const api = {
    // --- AUTHENTICATION ---
    login: async (email: string, password: string) => {
        const formData = new URLSearchParams();
        formData.append("username", email); // OAuth2PasswordRequestForm expects 'username'
        formData.append("password", password);

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Login failed");
        }
        return response.json(); // Returns { access_token, token_type }
    },

    register: async (email: string, password: string, fullName?: string, phone?: string, gender?: string, occupation?: string) => {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, full_name: fullName, phone, gender, occupation }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Registration failed");
        }
        return response.json(); // Returns { access_token, token_type }
    },

    logout: () => {
        localStorage.removeItem("access_token");
        window.location.href = "/";
    },

    // Get current user profile
    getMe: async () => {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            method: "GET",
            headers: getHeaders(),
        });
        if (!response.ok) throw new Error("Failed to fetch user profile");
        return response.json();
    },

    // --- REGISTRATION OTP ---
    verifyRegistration: async (email: string, otp: string) => {
        const response = await fetch(`${API_BASE_URL}/auth/verify-registration`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, otp }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Verification failed");
        }
        return response.json();
    },

    resendRegistrationOtp: async (email: string) => {
        const response = await fetch(`${API_BASE_URL}/auth/resend-registration-otp`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to resend OTP");
        }
        return response.json();
    },


    forgotPassword: async (email: string) => {
        const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to send reset code");
        }
        return response.json();
    },

    resetPassword: async (email: string, otp: string, newPassword: string) => {
        const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, otp, new_password: newPassword }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to reset password");
        }
        return response.json();
    },

    // --- GOOGLE OAUTH ---
    loginWithGoogle: async (credential: string) => {
        const response = await fetch(`${API_BASE_URL}/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ credential }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Google login failed");
        }
        return response.json(); // Returns { access_token, token_type }
    },

    // --- SESSION & DATA ---

    // 1. Upload File
    uploadFile: async (file: File) => {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${API_BASE_URL}/api/upload`, {
            method: "POST",
            headers: getHeaders(true), // isMultipart = true
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Upload failed");
        }
        return response.json(); // Returns SessionResponse
    },

    // 2. Get Dashboard Layout (UI Controller)
    getDashboard: async (sessionId: number) => {
        const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/dashboard`, {
            method: "GET",
            headers: getHeaders(),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to fetch dashboard");
        }
        return response.json(); // Returns UIControllerOutput
    },

    // 3. Chat with Data
    chat: async (sessionId: number, query: string) => {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ session_id: sessionId, query }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Chat failed");
        }
        return response.json(); // Returns { response: string, ... }
    },

    // 4. Get Chat Messages for a Session
    getSessionMessages: async (sessionId: number) => {
        const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/messages`, {
            method: "GET",
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error("Failed to fetch session messages");
        }
        return response.json(); // Returns MessageResponse[]
    },

    // 5. Get User History
    getHistory: async () => {
        const response = await fetch(`${API_BASE_URL}/api/history`, {
            method: "GET",
            headers: getHeaders(),
        });

        if (!response.ok) {
            // If 401, maybe redirect to login?
            if (response.status === 401) {
                throw new Error("Unauthorized");
            }
            throw new Error("Failed to fetch history");
        }
        return response.json();
    },

    // 6. Delete a session
    deleteSession: async (sessionId: number) => {
        const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}`, {
            method: "DELETE",
            headers: getHeaders(),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to delete session");
        }
        return response.json();
    }
};
