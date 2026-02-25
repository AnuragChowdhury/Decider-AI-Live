"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Lock, UserPlus, LogIn, Sparkles, ArrowLeft } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/services/api";
import { GoogleOAuthProvider, GoogleLogin } from "@react-oauth/google";

// Landing Components
import MouseTrace from "@/components/Landing/MouseTrace";
import Background from "@/components/Landing/Background";
import ScrollIndicator from "@/components/Landing/ScrollIndicator";
import Manifesto from "@/components/Landing/Manifesto";
import SalesTicker from "@/components/Landing/SalesTicker";
import AgentWorkflow from "@/components/Landing/AgentWorkflow";
import ValueProps from "@/components/Landing/ValueProps";
import TrustSection from "@/components/Landing/TrustSection";
import RevenueFunnel from "@/components/Landing/RevenueFunnel";
import DecisionMockups from "@/components/Landing/DecisionMockups";
import ImpactFloaters from "@/components/Landing/ImpactFloaters";
import DecisionGrid from "@/components/Landing/DecisionGrid";
import StrategicScanner from "@/components/Landing/StrategicScanner";
import DecisionFlow from "@/components/Landing/DecisionFlow";

export default function LandingPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [showAuth, setShowAuth] = useState(false);

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    phone: "",
    gender: "",
    occupation: "",
  });
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Forgot password state: idle | emailSent | done
  const [forgotStep, setForgotStep] = useState<"idle" | "emailSent" | "done">("idle");
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotOtp, setForgotOtp] = useState("");
  const [forgotNewPw, setForgotNewPw] = useState("");
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotError, setForgotError] = useState("");

  const handleForgotSendOtp = async (emailOverride?: string) => {
    const email = emailOverride ?? forgotEmail;
    if (!email) { setForgotError("Please enter your email first."); return; }
    setForgotLoading(true); setForgotError("");
    try {
      await api.forgotPassword(email);
      setForgotEmail(email);
      setForgotStep("emailSent");
    } catch (e: any) {
      setForgotError(e.message || "Failed to send code");
    } finally { setForgotLoading(false); }
  };

  const handleForgotReset = async () => {
    setForgotLoading(true); setForgotError("");
    try {
      await api.resetPassword(forgotEmail, forgotOtp, forgotNewPw);
      setForgotStep("done");
      setSuccessMsg("Password reset! Please sign in with your new password.");
      setForgotOtp(""); setForgotNewPw("");
    } catch (e: any) {
      setForgotError(e.message || "Reset failed");
    } finally { setForgotLoading(false); }
  };

  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      const response = await api.loginWithGoogle(credentialResponse.credential);
      localStorage.setItem("access_token", response.access_token);
      router.push("/workspace");
    } catch (e: any) {
      setError(e.message || "Google login failed");
    }
  };

  const resetForgotFlow = () => {
    setForgotStep("idle"); setForgotEmail(""); setForgotOtp("");
    setForgotNewPw(""); setForgotError("");
  };

  // Registration OTP verification
  const [regVerifyEmail, setRegVerifyEmail] = useState("");
  const [regVerifyOtp, setRegVerifyOtp] = useState("");
  const [regVerifyLoading, setRegVerifyLoading] = useState(false);
  const [regVerifyError, setRegVerifyError] = useState("");
  const [showRegVerify, setShowRegVerify] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  const handleVerifyRegistration = async () => {
    setRegVerifyLoading(true); setRegVerifyError("");
    try {
      await api.verifyRegistration(regVerifyEmail, regVerifyOtp);
      setShowRegVerify(false);
      setRegVerifyOtp(""); setRegVerifyEmail("");
      setSuccessMsg("Account verified! Please sign in.");
      setMode("login");
    } catch (e: any) {
      setRegVerifyError(e.message || "Verification failed");
    } finally { setRegVerifyLoading(false); }
  };

  const handleResendRegOtp = async () => {
    if (resendCooldown > 0) return;
    try {
      await api.resendRegistrationOtp(regVerifyEmail);
      setResendCooldown(60);
      // countdown
      const timer = setInterval(() => {
        setResendCooldown(prev => { if (prev <= 1) { clearInterval(timer); return 0; } return prev - 1; });
      }, 1000);
    } catch (e: any) {
      setRegVerifyError(e.message || "Failed to resend");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    setSuccessMsg("");

    try {
      if (mode === "login") {
        const response = await api.login(formData.email, formData.password);
        localStorage.setItem("access_token", response.access_token);
        router.push("/workspace");
      } else {
        // Registration: create account → show OTP verification step
        const result = await api.register(
          formData.email,
          formData.password,
          formData.full_name || undefined,
          formData.phone || undefined,
          formData.gender || undefined,
          formData.occupation || undefined,
        );
        setRegVerifyEmail(formData.email);
        setFormData({ email: "", password: "", full_name: "", phone: "", gender: "", occupation: "" });
        setShowRegVerify(true);
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white selection:bg-blue-500/30 overflow-x-hidden relative cursor-none font-sans">
      <MouseTrace />
      <Background />
      <ImpactFloaters />
      <DecisionGrid />
      <StrategicScanner />
      <DecisionFlow />

      {/* ── NAVIGATION ── */}
      <nav className="fixed top-0 left-0 right-0 z-[100] px-6 py-4 flex items-center justify-between backdrop-blur-md border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center shadow-lg shadow-white/10 overflow-hidden">
            <img src="/brand-icon.png" alt="DECIDER AI" className="w-6 h-6 object-contain" />
          </div>
          <span className="text-sm font-bold tracking-[0.2em] text-white font-sans uppercase opacity-80">DECIDER AI</span>
        </div>

        <div className="flex items-center gap-6">
          <button
            onClick={() => { setShowAuth(true); setMode("login"); }}
            className="text-sm font-medium text-zinc-400 hover:text-white transition-colors cursor-none"
          >
            Log In
          </button>
          <button
            onClick={() => { setShowAuth(true); setMode("register"); }}
            className="px-4 py-2 bg-white text-black text-sm font-bold rounded-xl hover:bg-zinc-200 transition-all cursor-none"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-6 text-center">
        <ScrollIndicator />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="max-w-4xl mx-auto space-y-6"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-full text-xs font-medium text-zinc-400 backdrop-blur-sm mb-4">
            <Sparkles className="w-3 h-3 text-blue-400" />
            The Future of Decision Intelligence
          </div>

          <h1 className="text-5xl md:text-7xl font-black tracking-[-0.05em] leading-[0.85] text-white">
            The Neural Link for<br />
            <span className="bg-gradient-to-b from-white via-white to-white/20 bg-clip-text text-transparent">
              Sales Intelligence
            </span><br />
            <span className="bg-gradient-to-r from-blue-500 to-cyan-400 bg-clip-text text-transparent text-2xl md:text-5xl font-bold tracking-tight mt-6 block italic text-center">
              Autonomous Revenue Autonomy
            </span>
          </h1>

          <p className="text-zinc-500 text-base md:text-xl max-w-2xl mx-auto leading-relaxed font-medium mt-6">
            Your <span className="text-zinc-100">messy CRM data</span>, autonomously fused into <span className="text-blue-400/80">forensic pipeline intelligence</span>.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => { setShowAuth(true); setMode("register"); }}
              className="group px-8 py-4 bg-white text-black font-bold rounded-2xl flex items-center gap-2 justify-center hover:bg-zinc-100 transition-all cursor-none"
            >
              <UserPlus className="w-4 h-4" />
              Start Free
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => { setShowAuth(true); setMode("login"); }}
              className="px-8 py-4 border border-white/10 text-white font-medium rounded-2xl flex items-center gap-2 justify-center hover:border-white/30 hover:bg-white/5 transition-all cursor-none"
            >
              <LogIn className="w-4 h-4" />
              Sign In
            </motion.button>
          </div>
        </motion.div>
      </section>

      {/* ── LANDING SECTIONS ── */}
      <Manifesto />
      <SalesTicker />
      <AgentWorkflow />
      <ValueProps />
      <DecisionMockups />
      <TrustSection />
      <RevenueFunnel />

      {/* ── AUTH MODAL ── */}
      <AnimatePresence>
        {showAuth && (
          <motion.div
            key="auth-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm cursor-none"
            onClick={(e) => { if (e.target === e.currentTarget) { setShowAuth(false); resetForgotFlow(); setError(""); setSuccessMsg(""); } }}
          >
            <motion.div
              key="auth-panel"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-zinc-900 border border-white/10 p-8 rounded-3xl w-full max-w-md shadow-2xl relative overflow-y-auto max-h-[90vh]"
            >
              {/* Close */}
              <button
                onClick={() => { setShowAuth(false); resetForgotFlow(); setError(""); setSuccessMsg(""); }}
                className="absolute top-4 right-4 text-zinc-500 hover:text-white transition-colors cursor-none"
              >
                ✕
              </button>

              <div className="text-center mb-8">
                <div className="inline-flex items-center gap-2 mb-3">
                  <Lock className="w-4 h-4 text-zinc-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-1">Access Portal</h2>
                <p className="text-zinc-500 text-sm">Enterprise-grade intelligence awaits.</p>
              </div>

              {/* ── REGISTRATION OTP VERIFICATION ── */}
              {showRegVerify ? (
                <div className="space-y-4">
                  <div className="text-center mb-4">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-500/10 border border-green-500/20 mb-3">
                      <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-bold text-white">Verify Your Account</h3>
                    <p className="text-zinc-500 text-xs mt-1">
                      We sent a 6-digit code to your <strong className="text-white">email</strong>
                      {regVerifyEmail.includes("@") ? "" : ""}{" "}
                      {/* show phone hint if we had it */}
                      and <strong className="text-white">phone</strong> (if provided). Enter either code below.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-1">Verification Code</label>
                    <input
                      type="text"
                      maxLength={6}
                      placeholder="123456"
                      value={regVerifyOtp}
                      onChange={(e) => setRegVerifyOtp(e.target.value.replace(/\D/g, ""))}
                      className="w-full bg-black/50 border border-white/5 text-white rounded-xl py-3 px-4 tracking-widest text-center text-2xl font-mono focus:outline-none focus:border-green-500/50 transition-all cursor-none"
                      autoFocus
                    />
                  </div>

                  {regVerifyError && (
                    <div className="text-red-400 text-xs px-2 py-2 bg-red-500/5 border border-red-500/10 rounded-lg">{regVerifyError}</div>
                  )}

                  <button
                    onClick={handleVerifyRegistration}
                    disabled={regVerifyLoading || regVerifyOtp.length < 6}
                    className="w-full bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white font-bold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2 cursor-none"
                  >
                    {regVerifyLoading
                      ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      : "Verify Account"}
                  </button>

                  <button
                    onClick={handleResendRegOtp}
                    disabled={resendCooldown > 0}
                    className="w-full text-xs text-zinc-500 hover:text-white disabled:opacity-40 py-1 cursor-none transition-colors"
                  >
                    {resendCooldown > 0 ? `Resend code in ${resendCooldown}s` : "Resend code"}
                  </button>
                </div>

              ) : (
                <>
                  {/* ── FORGOT PASSWORD STEP: OTP entry ── */}
                  {forgotStep === "emailSent" ? (

                    <div className="space-y-4">
                      <button
                        onClick={resetForgotFlow}
                        className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-white mb-2 cursor-none"
                      >
                        <ArrowLeft className="w-3 h-3" /> Back to login
                      </button>
                      <div className="text-center mb-4">
                        <h3 className="text-lg font-bold text-white">Reset Password</h3>
                        <p className="text-zinc-500 text-xs mt-1">
                          Enter the 6-digit code we emailed to <strong className="text-white">{forgotEmail}</strong>, then choose a new password.
                        </p>
                      </div>

                      <div className="space-y-2">
                        <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-1">Reset Code</label>
                        <input
                          type="text"
                          maxLength={6}
                          placeholder="123456"
                          value={forgotOtp}
                          onChange={(e) => setForgotOtp(e.target.value.replace(/\D/g, ""))}
                          className="w-full bg-black/50 border border-white/5 text-white rounded-xl py-3 px-4 tracking-widest text-center text-xl font-mono focus:outline-none focus:border-blue-500/50 transition-all cursor-none"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-1">New Password</label>
                        <input
                          type="password"
                          placeholder="••••••••"
                          value={forgotNewPw}
                          onChange={(e) => setForgotNewPw(e.target.value)}
                          className="w-full bg-black/50 border border-white/5 text-white rounded-xl py-3 px-4 focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-zinc-800 cursor-none"
                        />
                      </div>

                      {forgotError && (
                        <div className="text-red-400 text-xs px-2 py-2 bg-red-500/5 border border-red-500/10 rounded-lg">{forgotError}</div>
                      )}

                      <button
                        onClick={handleForgotReset}
                        disabled={forgotLoading || forgotOtp.length < 6 || !forgotNewPw}
                        className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2 cursor-none mt-2"
                      >
                        {forgotLoading
                          ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          : "Reset Password"}
                      </button>

                      <button
                        onClick={() => handleForgotSendOtp()}
                        disabled={forgotLoading}
                        className="w-full text-xs text-zinc-500 hover:text-white py-1 cursor-none"
                      >
                        Resend code
                      </button>
                    </div>

                  ) : forgotStep === "done" ? (
                    // After successful reset, show success and flip back to login view
                    <div className="space-y-4">
                      {successMsg && (
                        <div className="text-green-400 text-xs px-3 py-2.5 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-2">
                          <svg className="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          {successMsg}
                        </div>
                      )}
                      <button
                        onClick={() => { resetForgotFlow(); setMode("login"); }}
                        className="w-full bg-white text-black font-bold py-3.5 rounded-xl hover:bg-zinc-200 transition-all cursor-none"
                      >
                        Back to Sign In
                      </button>
                    </div>

                  ) : (
                    // ── NORMAL LOGIN / REGISTER VIEW ──
                    <>
                      {/* Tabs */}
                      <div className="flex bg-black/40 rounded-xl p-1 mb-6 border border-white/5">
                        <button
                          onClick={() => { setMode("login"); setError(""); setSuccessMsg(""); }}
                          className={`flex-1 py-2 text-xs font-medium rounded-lg transition-all cursor-none ${mode === "login" ? "bg-white text-black shadow-md" : "text-gray-500 hover:text-white"}`}
                        >
                          Login
                        </button>
                        <button
                          onClick={() => { setMode("register"); setError(""); setSuccessMsg(""); }}
                          className={`flex-1 py-2 text-xs font-medium rounded-lg transition-all cursor-none ${mode === "register" ? "bg-white text-black shadow-md" : "text-gray-500 hover:text-white"}`}
                        >
                          Register
                        </button>
                      </div>

                      {/* Google Sign-In */}
                      <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ""}>
                        <div className="mb-4 flex justify-center">
                          <GoogleLogin
                            onSuccess={handleGoogleSuccess}
                            onError={() => setError("Google sign-in failed. Please try again.")}
                            theme="filled_black"
                            shape="rectangular"
                            size="large"
                            width="368"
                            text={mode === "login" ? "signin_with" : "signup_with"}
                          />
                        </div>
                      </GoogleOAuthProvider>

                      {/* Divider */}
                      <div className="flex items-center gap-3 mb-5">
                        <div className="flex-1 h-px bg-white/5" />
                        <span className="text-[10px] text-zinc-600 uppercase tracking-widest">or continue with email</span>
                        <div className="flex-1 h-px bg-white/5" />
                      </div>

                      {/* Email / Password Form */}
                      <form onSubmit={handleSubmit} className="space-y-4">
                        {mode === "register" && (
                          <div className="space-y-2">
                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-1">Full Name</label>
                            <input
                              type="text"
                              placeholder="Jane Doe"
                              value={formData.full_name}
                              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                              className="w-full bg-black/50 border border-white/5 text-white rounded-xl py-3 px-4 focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-zinc-800 cursor-none"
                            />
                          </div>
                        )}

                        <div className="space-y-2">
                          <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-1">Email</label>
                          <input
                            type="email"
                            placeholder="name@company.com"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            className="w-full bg-black/50 border border-white/5 text-white rounded-xl py-3 px-4 focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-zinc-800 cursor-none"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between px-1">
                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Password</label>
                            {mode === "login" && (
                              <button
                                type="button"
                                onClick={() => handleForgotSendOtp(formData.email)}
                                className="text-[10px] text-blue-400 hover:text-blue-300 cursor-none transition-colors"
                              >
                                Forgot password?
                              </button>
                            )}
                          </div>
                          <input
                            type="password"
                            placeholder="••••••••"
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            className="w-full bg-black/50 border border-white/5 text-white rounded-xl py-3 px-4 focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-zinc-800 cursor-none"
                            required
                          />
                        </div>

                        {mode === "register" && (
                          <>
                            <div className="grid grid-cols-2 gap-3">
                              <div className="space-y-2">
                                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-1">Phone</label>
                                <input
                                  type="tel"
                                  placeholder="+91 9876543210"
                                  value={formData.phone}
                                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                  className="w-full bg-black/50 border border-white/5 text-white rounded-xl py-3 px-4 focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-zinc-800 cursor-none text-sm"
                                />
                              </div>
                              <div className="space-y-2">
                                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-1">Gender</label>
                                <select
                                  value={formData.gender}
                                  onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                                  className="w-full bg-black/50 border border-white/5 text-white rounded-xl py-3 px-4 focus:outline-none focus:border-blue-500/50 transition-all cursor-none text-sm"
                                >
                                  <option value="" className="bg-zinc-900">Select...</option>
                                  <option value="Male" className="bg-zinc-900">Male</option>
                                  <option value="Female" className="bg-zinc-900">Female</option>
                                  <option value="Non-binary" className="bg-zinc-900">Non-binary</option>
                                  <option value="Prefer not to say" className="bg-zinc-900">Prefer not to say</option>
                                </select>
                              </div>
                            </div>
                            <div className="space-y-2">
                              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-1">Occupation</label>
                              <input
                                type="text"
                                placeholder="e.g. Data Analyst, Sales Manager"
                                value={formData.occupation}
                                onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                                className="w-full bg-black/50 border border-white/5 text-white rounded-xl py-3 px-4 focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-zinc-800 cursor-none text-sm"
                              />
                            </div>
                          </>
                        )}

                        {successMsg && (
                          <div className="text-green-400 text-xs px-3 py-2.5 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-2">
                            <svg className="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            {successMsg}
                          </div>
                        )}

                        {error && (
                          <div className="text-red-400 text-xs px-2 py-2 bg-red-500/5 border border-red-500/10 rounded-lg">{error}</div>
                        )}

                        <button
                          type="submit"
                          disabled={isLoading}
                          className="w-full bg-white text-black font-bold py-4 rounded-xl hover:bg-zinc-200 transition-all flex items-center justify-center gap-2 mt-4 cursor-none"
                        >
                          {isLoading
                            ? <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                            : mode === "login" ? "Sign In" : "Create Account"}
                        </button>
                      </form>
                    </>
                  )}
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
