import React, { useState } from "react";
import {
  LoadingSpinner,
  InlineSpinner,
  ButtonSpinner,
  LoadingCard,
  LoadingSkeleton,
} from "../components/LoadingSpinner";

const SpinnersShowcase = () => {
  const [activeSpinner, setActiveSpinner] = useState("default");

  const spinnerTypes = [
    {
      id: "default",
      name: "Default Spinner",
      description: "Classic rotating loader with icon",
    },
    {
      id: "ring",
      name: "Ring Spinner",
      description: "Rotating ring border effect",
    },
    {
      id: "dots",
      name: "Dots Spinner",
      description: "Bouncing dots animation",
    },
    { id: "wave", name: "Wave Spinner", description: "Wave bar animation" },
    {
      id: "pulse",
      name: "Pulse Spinner",
      description: "Pulsing circle effect",
    },
    {
      id: "blob",
      name: "Blob Spinner",
      description: "Morphing blob animation",
    },
    { id: "glow", name: "Glow Spinner", description: "Glowing expanding ring" },
  ];

  return (
    <div className="min-h-screen bg-black relative overflow-hidden p-8">
      <div className="blob blob-1 opacity-10" />
      <div className="blob blob-2 opacity-10" />

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16 fade-in">
          <h1 className="text-6xl font-black mb-4 leading-[1.1] tracking-tighter">
            Loading <span className="primary-gradient-text">Spinners</span>
          </h1>
          <p className="max-w-md mx-auto text-gray-500 text-sm font-medium">
            Multiple spinner variations for all your loading states.
          </p>
        </div>

        {/* Main Showcase */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-16">
          {/* Spinner Display */}
          <div className="lg:col-span-2">
            <div className="glass rounded-2xl p-12 border-white/10 flex items-center justify-center min-h-64">
              <LoadingSpinner
                type={activeSpinner}
                size="lg"
                text={`${spinnerTypes.find((s) => s.id === activeSpinner)?.name} Active`}
              />
            </div>
          </div>

          {/* Spinner Selector */}
          <div className="space-y-4">
            <div className="glass rounded-2xl p-6 border-white/10">
              <h3 className="text-sm font-black text-white mb-4 uppercase tracking-widest">
                Spinner Types
              </h3>
              <div className="space-y-2">
                {spinnerTypes.map((spinner) => (
                  <button
                    key={spinner.id}
                    onClick={() => setActiveSpinner(spinner.id)}
                    className={`w-full text-left p-3 rounded-xl transition-all text-xs font-black uppercase tracking-wider ${
                      activeSpinner === spinner.id
                        ? "bg-primary text-black border border-primary"
                        : "bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10"
                    }`}
                  >
                    <div className="font-bold">{spinner.name}</div>
                    <div className="text-[10px] opacity-75">
                      {spinner.description}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Size Showcase */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          {/* Sizes */}
          <div className="glass rounded-2xl p-8 border-white/10">
            <h3 className="text-sm font-black text-white mb-8 uppercase tracking-widest">
              Spinner Sizes
            </h3>
            <div className="flex items-center justify-around gap-8">
              {["sm", "md", "lg", "xl"].map((size) => (
                <div key={size} className="flex flex-col items-center gap-4">
                  <LoadingSpinner type={activeSpinner} size={size} text="" />
                  <span className="text-xs font-black text-gray-500 uppercase">
                    {size}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Inline Usage */}
          <div className="glass rounded-2xl p-8 border-white/10">
            <h3 className="text-sm font-black text-white mb-8 uppercase tracking-widest">
              Inline Spinner
            </h3>
            <div className="space-y-6">
              <div className="text-sm text-gray-300">
                <span>Loading data</span>
                <InlineSpinner />
              </div>
              <div className="text-sm text-gray-300">
                <span>Fetching results</span>
                <InlineSpinner />
              </div>
            </div>
          </div>
        </div>

        {/* Components Showcase */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          {/* Loading Card */}
          <div>
            <h3 className="text-sm font-black text-white mb-4 uppercase tracking-widest">
              Loading Card
            </h3>
            <LoadingCard size="md" />
          </div>

          {/* Button States */}
          <div>
            <h3 className="text-sm font-black text-white mb-4 uppercase tracking-widest">
              Button States
            </h3>
            <div className="glass rounded-2xl p-8 border-white/10 space-y-4">
              <ButtonSpinner loading={false}>Ready to Go</ButtonSpinner>
              <ButtonSpinner loading={true}>Processing</ButtonSpinner>
              <ButtonSpinner loading={false} disabled={true}>
                Disabled
              </ButtonSpinner>
            </div>
          </div>
        </div>

        {/* Loading Skeleton */}
        <div className="glass rounded-2xl p-8 border-white/10 mb-16">
          <h3 className="text-sm font-black text-white mb-6 uppercase tracking-widest">
            Loading Skeleton
          </h3>
          <LoadingSkeleton rows={3} columns={2} />
        </div>

        {/* Full Screen Overlay */}
        <div className="glass rounded-2xl p-8 border-white/10">
          <h3 className="text-sm font-black text-white mb-6 uppercase tracking-widest">
            Full Screen Overlay
          </h3>
          <p className="text-xs text-gray-400 mb-6">
            Use fullScreen prop to show spinner as overlay
          </p>
          <div className="relative w-full h-48 rounded-xl bg-white/5 flex items-center justify-center border border-white/10">
            <div className="absolute inset-0 bg-black/50 rounded-xl flex items-center justify-center">
              <LoadingSpinner
                type={activeSpinner}
                size="md"
                text="Full Screen Mode"
                fullScreen={false}
              />
            </div>
            <span className="text-xs text-gray-600 font-black uppercase">
              Content Layer
            </span>
          </div>
        </div>

        {/* Code Examples */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-16">
          <div className="glass rounded-2xl p-6 border-white/10">
            <h3 className="text-xs font-black text-primary mb-4 uppercase tracking-widest">
              Basic Usage
            </h3>
            <pre className="text-[10px] text-gray-400 overflow-x-auto">
              {`import { LoadingSpinner } from '@/components'

<LoadingSpinner 
  type="ring" 
  size="md" 
  text="Loading..." 
/>`}
            </pre>
          </div>

          <div className="glass rounded-2xl p-6 border-white/10">
            <h3 className="text-xs font-black text-primary mb-4 uppercase tracking-widest">
              Variants
            </h3>
            <pre className="text-[10px] text-gray-400 overflow-x-auto">
              {`// Different types
'default' | 'ring' | 'dots'
'wave' | 'pulse' | 'blob'

// Sizes
'sm' | 'md' | 'lg' | 'xl'`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpinnersShowcase;
