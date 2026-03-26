import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabase";
import {
  UserPlus,
  Mail,
  Lock,
  User,
  Phone,
  Hash,
  Zap,
  Loader2,
  AlertCircle,
  Globe,
  GraduationCap,
} from "lucide-react";

const Register = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    phone: "",
    roll_number: "",
    section: "",
    branch: "",
    year: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: formData.email,
        password: formData.password,
      });

      if (authError) throw authError;

      if (authData?.user) {
        // BUG #9 fix: Check if a user with this phone already exists (WhatsApp registration)
        // If so, link the auth_user_id instead of creating a duplicate
        const { data: existingUser } = await supabase
          .from("Auto_bot")
          .select("*")
          .eq("phone_number", formData.phone)
          .single();

        if (existingUser) {
          // User registered via WhatsApp — link their auth_user_id
          const { error: linkError } = await supabase
            .from("Auto_bot")
            .update({
              auth_user_id: authData.user.id,
              name: formData.name,
              email: formData.email,
              roll_number: formData.roll_number,
              section: formData.section,
              branch: formData.branch,
              year: formData.year,
            })
            .eq("phone_number", formData.phone);

          if (linkError) throw linkError;
        } else {
          // Brand new user — insert fresh record
          const { error: profileError } = await supabase
            .from("Auto_bot")
            .insert({
              auth_user_id: authData.user.id,
              phone_number: formData.phone,
              name: formData.name,
              roll_number: formData.roll_number,
              section: formData.section,
              branch: formData.branch,
              year: formData.year,
              email: formData.email,
            });

          if (profileError) throw profileError;
        }
        navigate("/");
      }
    } catch (err) {
      console.error("Registration error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black relative overflow-hidden flex flex-col items-center justify-center p-4 py-20">
      <div className="blob blob-1" />
      <div className="blob blob-2" />

      {/* Industrial-Grade Auth Terminal */}
      <div className="relative z-10 fade-in auth-terminal-width">
        {/* Floating Top Icon: Enforced Centering */}
        <div className="absolute -top-8 left-1/2 -translate-x-1/2 z-20">
          <div className="w-20 h-20 bg-white rounded-3xl flex items-center justify-center shadow-icon border border-white/10 transition-all duration-300">
            <UserPlus className="text-black" size={32} />
          </div>
        </div>

        <div className="glass p-10 pt-20 rounded-[3.5rem] border-white/10 relative overflow-hidden shadow-2xl flex flex-col items-center">
          <div className="text-center mb-10">
            <h1 className="text-2xl font-black text-white mb-2 uppercase tracking-tighter">
              Create Account
            </h1>
            <p className="text-gray-500 text-xs font-medium">
              Join the intelligent automation platform.
            </p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-500 p-4 rounded-xl mb-8 flex items-center gap-3 text-xs font-black uppercase tracking-widest animate-pulse w-full">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <form
            onSubmit={handleRegister}
            className="space-y-6 w-full relative z-10 text-left"
          >
            <div className="space-y-5">
              <div className="space-y-2">
                <label className="text-xs font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                  Name
                </label>
                <div className="relative group">
                  <div className="transform-v-center left-5 z-20 pointer-events-none">
                    <User size={18} className="text-primary" />
                  </div>
                  <input
                    type="text"
                    placeholder="Full Name"
                    className="w-full bg-white/5 border-white/5 pl-14 pr-6 py-4 rounded-2xl text-sm focus:bg-white/10 transition-all font-medium"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                  Email
                </label>
                <div className="relative group">
                  <div className="transform-v-center left-5 z-20 pointer-events-none">
                    <Mail size={18} className="text-primary" />
                  </div>
                  <input
                    type="email"
                    placeholder="name@example.com"
                    className="w-full bg-white/5 border-white/5 pl-14 pr-6 py-4 rounded-2xl text-sm focus:bg-white/10 transition-all font-medium"
                    value={formData.email}
                    onChange={(e) =>
                      setFormData({ ...formData, email: e.target.value })
                    }
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                  Key
                </label>
                <div className="relative group">
                  <div className="transform-v-center left-5 z-20 pointer-events-none">
                    <Lock size={18} className="text-primary" />
                  </div>
                  <input
                    type="password"
                    placeholder="Password"
                    className="w-full bg-white/5 border-white/5 pl-14 pr-6 py-4 rounded-2xl text-sm focus:bg-white/10 transition-all font-medium"
                    value={formData.password}
                    onChange={(e) =>
                      setFormData({ ...formData, password: e.target.value })
                    }
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                  Phone
                </label>
                <div className="relative group">
                  <div className="transform-v-center left-5 z-20 pointer-events-none">
                    <Phone size={18} className="text-primary" />
                  </div>
                  <input
                    type="text"
                    placeholder="+91 XXXXX XXXXX"
                    className="w-full bg-white/5 border-white/5 pl-14 pr-6 py-4 rounded-2xl text-sm focus:bg-white/10 transition-all font-medium"
                    value={formData.phone}
                    onChange={(e) =>
                      setFormData({ ...formData, phone: e.target.value })
                    }
                    required
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6 pt-2">
              <div className="space-y-2">
                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                  Roll No
                </label>
                <input
                  type="text"
                  placeholder="ID"
                  className="w-full bg-white/5 border-white/5 px-4 py-4 rounded-xl text-xs focus:bg-white/10 transition-all font-medium"
                  value={formData.roll_number}
                  onChange={(e) =>
                    setFormData({ ...formData, roll_number: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                  Branch
                </label>
                <input
                  type="text"
                  placeholder="Dept"
                  className="w-full bg-white/5 border-white/5 px-4 py-4 rounded-xl text-xs focus:bg-white/10 transition-all font-medium"
                  value={formData.branch}
                  onChange={(e) =>
                    setFormData({ ...formData, branch: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                  Section
                </label>
                <input
                  type="text"
                  placeholder="Sec"
                  className="w-full bg-white/5 border-white/5 px-4 py-4 rounded-xl text-xs focus:bg-white/10 transition-all font-medium"
                  value={formData.section}
                  onChange={(e) =>
                    setFormData({ ...formData, section: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                  Year
                </label>
                <input
                  type="text"
                  placeholder="1"
                  className="w-full bg-white/5 border-white/5 px-4 py-4 rounded-xl text-xs focus:bg-white/10 transition-all font-medium"
                  value={formData.year}
                  onChange={(e) =>
                    setFormData({ ...formData, year: e.target.value })
                  }
                  required
                />
              </div>
            </div>

            <div className="pt-8">
              <button
                type="submit"
                className="w-full h-14 bg-white text-black text-sm font-black uppercase tracking-widest shadow-2xl rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    Creating...
                  </>
                ) : (
                  "Sign Up"
                )}
              </button>
            </div>
          </form>

          <div className="mt-10 pt-8 border-t border-white/5 text-center w-full">
            <p className="text-gray-500 font-black text-[10px] uppercase tracking-widest">
              Already have an account?{" "}
              <Link
                to="/login"
                className="text-primary hover:text-white transition-colors ml-1"
              >
                Sign In
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
