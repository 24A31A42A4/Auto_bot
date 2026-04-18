import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import {
  User,
  Phone,
  Mail,
  Award,
  Save,
  Loader2,
  ChevronLeft,
  Hash,
  Activity,
  ShieldCheck,
  Cpu,
  MapPin,
  GraduationCap,
  Edit3,
  AlertCircle,
} from "lucide-react";
import { Link } from "react-router-dom";
import { LoadingSpinner, LoadingCard } from "../components/LoadingSpinner";

const API_URL = import.meta.env.VITE_API_URL || "/_/backend";

const Profile = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const [profile, setProfile] = useState({
    name: "",
    phone_number: "",
    email: "",
    roll_number: "",
    section: "",
    branch: "",
    year: "",
  });

  const fetchProfile = useCallback(async () => {
    if (!user) return;
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/profile/${user.id}`);

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setMessage({
          type: "error",
          text: errData.detail || "Failed to load profile",
        });
        return;
      }

      const data = await res.json();
      if (data) {
        setProfile({
          name: data.name || "",
          phone_number: data.phone_number || "",
          email: data.email || "",
          roll_number: data.roll_number || "",
          section: data.section || "",
          branch: data.branch || "",
          year: data.year || "",
        });
      }
    } catch (err) {
      console.error("Error fetching profile:", err);
      setMessage({
        type: "error",
        text: "Cannot connect to server. Is the backend running?",
      });
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      fetchProfile();
    }
  }, [user, fetchProfile]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      const res = await fetch(`${API_URL}/profile/${user.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: profile.name,
          email: profile.email,
          section: profile.section,
          branch: profile.branch,
          year: profile.year,
          roll_number: profile.roll_number,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Update failed");
      }

      setMessage({ type: "success", text: "Saved Successfully" });
      fetchProfile();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setSaving(false);
    }
  };

  if (loading)
    return (
      <div className="min-h-screen flex items-center justify-center bg-black relative overflow-hidden">
        <div className="blob blob-1 opacity-15" />
        <div className="blob blob-2 opacity-15" />
        <div className="relative z-10">
          <LoadingCard size="lg" />
        </div>
      </div>
    );

  return (
    <div className="bg-black min-h-screen relative overflow-hidden flex flex-col items-center pt-32 pb-20 px-4">
      <div className="blob blob-1" />
      <div className="blob blob-2" />

      <div className="w-full max-w-2xl relative z-10 fade-in">
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary/10 border border-primary/30 text-[10px] font-black uppercase tracking-[0.2em] text-primary hover:text-black hover:bg-primary transition-all mb-12 group shadow-[0_0_20px_rgba(0,191,255,0.1)]"
        >
          <ChevronLeft
            size={14}
            className="group-hover:-translate-x-1 transition-transform"
          />
          Return to Dashboard
        </Link>

        {/* Global Identity Card */}
        <div className="glass rounded-[3.5rem] border-white/10 overflow-hidden shadow-2xl">
          {/* Top Banner: Profile Info */}
          <div className="p-10 border-b border-white/5 bg-white/5 flex flex-col items-center text-center">
            <div className="relative mb-6">
              <div className="w-24 h-24 rounded-3xl bg-black border border-white/10 flex items-center justify-center shadow-inner group-hover:scale-105 transition-all">
                <User className="text-gray-800" size={48} />
              </div>
            </div>

            <h2 className="text-3xl font-black tracking-tighter uppercase mb-2">
              {profile.name || "Anonymous"}
            </h2>
            <div className="flex items-center gap-4 text-[10px] text-gray-500 font-black uppercase tracking-widest mb-10">
              <span className="w-1 h-1 rounded-full bg-white/10" />
            </div>
          </div>

          {/* Form Content */}
          <div className="p-10 md:p-14">
            <div className="flex items-center gap-3 mb-10">
              <ShieldCheck className="text-primary" size={20} />
              <h3 className="text-sm font-black uppercase tracking-[0.3em]">
                Your Profile
              </h3>
            </div>

            <form onSubmit={handleUpdate} className="space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <User size={12} /> Full Name
                  </label>
                  <input
                    type="text"
                    value={profile.name}
                    onChange={(e) =>
                      setProfile({ ...profile, name: e.target.value })
                    }
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="Enter Name"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <Mail size={12} className="text-primary" /> Email Address
                  </label>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={(e) =>
                      setProfile({ ...profile, email: e.target.value })
                    }
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="name@example.com"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <Phone size={12} className="text-primary" /> Phone Number
                    <span className="text-[8px] text-gray-600 normal-case tracking-normal ml-1">
                      (read-only)
                    </span>
                  </label>
                  <input
                    type="text"
                    value={profile.phone_number}
                    readOnly
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full font-mono opacity-60 cursor-not-allowed"
                    placeholder="+91 XXXXX XXXXX"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <Hash size={12} /> Roll Number
                  </label>
                  <input
                    type="text"
                    value={profile.roll_number}
                    onChange={(e) =>
                      setProfile({ ...profile, roll_number: e.target.value })
                    }
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="Enter Roll No"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <Cpu size={12} /> Branch
                  </label>
                  <input
                    type="text"
                    value={profile.branch}
                    onChange={(e) =>
                      setProfile({ ...profile, branch: e.target.value })
                    }
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="e.g. AIML"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <MapPin size={12} /> Section
                  </label>
                  <input
                    type="text"
                    value={profile.section}
                    onChange={(e) =>
                      setProfile({ ...profile, section: e.target.value })
                    }
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="e.g. A"
                  />
                </div>
                <div className="space-y-3 md:col-span-2">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <GraduationCap size={12} /> Academic Year
                  </label>
                  <input
                    type="text"
                    value={profile.year}
                    onChange={(e) =>
                      setProfile({ ...profile, year: e.target.value })
                    }
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="e.g. 2nd Year"
                  />
                </div>
              </div>

              <div className="flex flex-col items-center pt-10">
                {message && (
                  <div
                    className={`mb-6 p-4 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-3 w-full justify-center ${message.type === "success" ? "bg-primary/10 text-primary border border-primary/20" : "bg-red-500/10 text-red-500 border border-red-500/20"}`}
                  >
                    {message.type === "success" ? (
                      <ShieldCheck size={16} />
                    ) : (
                      <AlertCircle size={16} />
                    )}
                    {message.text}
                  </div>
                )}
                <button
                  type="submit"
                  className="w-full md:w-fit px-12 h-14 text-[11px] font-black uppercase tracking-widest shadow-2xl rounded-2xl flex items-center justify-center gap-2 bg-transparent border-2 border-primary text-primary hover:bg-primary/10 hover:text-white active:bg-primary/20 active:text-white focus:outline-none focus:ring-0 transition-all disabled:opacity-50"
                  disabled={saving}
                >
                  {saving ? (
                    <>
                      <Loader2 className="animate-spin" size={18} />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save size={18} />
                      Save Changes
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>

        <p className="mt-12 text-center text-[10px] font-black text-gray-800 uppercase tracking-[0.5em] leading-loose">
          Profile Management
        </p>
      </div>
    </div>
  );
};

export default Profile;
