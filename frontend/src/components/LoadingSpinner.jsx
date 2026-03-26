import React from "react";
import { Loader2 } from "lucide-react";

/**
 * LoadingSpinner Component
 * Multiple spinner variations for loading states
 *
 * @param {string} type - Spinner type: 'default', 'ring', 'dots', 'wave', 'pulse', 'blob'
 * @param {string} size - Size: 'sm', 'md', 'lg', 'xl'
 * @param {string} text - Loading text to display
 * @param {boolean} fullScreen - Show as full screen overlay
 * @param {string} color - Primary color override
 */
export const LoadingSpinner = ({
  type = "default",
  size = "md",
  text = "Loading...",
  fullScreen = false,
  color = "#00bfff",
}) => {
  // Get size dimensions
  const sizeMap = {
    sm: "w-6 h-6",
    md: "w-8 h-8",
    lg: "w-12 h-12",
    xl: "w-16 h-16",
  };

  // Default Spinner with Loader2 icon
  if (type === "default") {
    return (
      <div className={fullScreen ? "loading-overlay" : "loader-container"}>
        <div className={`${fullScreen ? "loading-overlay-content" : ""}`}>
          <Loader2 className={`${sizeMap[size]} animate-spin text-primary`} />
          {text && (
            <span
              className={`${fullScreen ? "loading-text" : "text-xs text-gray-500"}`}
            >
              {text}
            </span>
          )}
        </div>
      </div>
    );
  }

  // Ring Spinner
  if (type === "ring") {
    const ringSize = {
      sm: "spinner-ring-sm",
      md: "spinner-ring-md",
      lg: "spinner-ring-lg",
      xl: "w-24 h-24",
    };
    return (
      <div className={fullScreen ? "loading-overlay" : "loader-container"}>
        <div className={`${fullScreen ? "loading-overlay-content" : ""}`}>
          <div className={`spinner-ring ${ringSize[size]}`} />
          {text && (
            <span
              className={`${fullScreen ? "loading-text" : "text-xs text-gray-500"}`}
            >
              {text}
            </span>
          )}
        </div>
      </div>
    );
  }

  // Dots Spinner
  if (type === "dots") {
    return (
      <div className={fullScreen ? "loading-overlay" : "loader-container"}>
        <div className={`${fullScreen ? "loading-overlay-content" : ""}`}>
          <div className="spinner-dots flex gap-1">
            <div className={`${sizeMap[size]} bg-primary rounded-full`} />
            <div className={`${sizeMap[size]} bg-primary rounded-full`} />
            <div className={`${sizeMap[size]} bg-primary rounded-full`} />
          </div>
          {text && (
            <span
              className={`${fullScreen ? "loading-text" : "text-xs text-gray-500"}`}
            >
              {text}
            </span>
          )}
        </div>
      </div>
    );
  }

  // Wave Spinner
  if (type === "wave") {
    const barSize =
      size === "sm"
        ? "2px"
        : size === "md"
          ? "3px"
          : size === "lg"
            ? "4px"
            : "5px";
    return (
      <div className={fullScreen ? "loading-overlay" : "loader-container"}>
        <div className={`${fullScreen ? "loading-overlay-content" : ""}`}>
          <div className="spinner-wave flex gap-1 items-end">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="bg-primary rounded-full"
                style={{
                  width: barSize,
                  height: barSize,
                }}
              />
            ))}
          </div>
          {text && (
            <span
              className={`${fullScreen ? "loading-text" : "text-xs text-gray-500"}`}
            >
              {text}
            </span>
          )}
        </div>
      </div>
    );
  }

  // Pulse Spinner
  if (type === "pulse") {
    return (
      <div className={fullScreen ? "loading-overlay" : "loader-container"}>
        <div className={`${fullScreen ? "loading-overlay-content" : ""}`}>
          <div
            className={`${sizeMap[size]} bg-primary rounded-full spinner-pulse`}
          />
          {text && (
            <span
              className={`${fullScreen ? "loading-text" : "text-xs text-gray-500"}`}
            >
              {text}
            </span>
          )}
        </div>
      </div>
    );
  }

  // Blob Spinner
  if (type === "blob") {
    return (
      <div className={fullScreen ? "loading-overlay" : "loader-container"}>
        <div className={`${fullScreen ? "loading-overlay-content" : ""}`}>
          <div
            className={`${sizeMap[size]} bg-primary rounded-full spinner-blob`}
            style={{
              filter: "blur(1px)",
            }}
          />
          {text && (
            <span
              className={`${fullScreen ? "loading-text" : "text-xs text-gray-500"}`}
            >
              {text}
            </span>
          )}
        </div>
      </div>
    );
  }

  // Glow Spinner
  if (type === "glow") {
    return (
      <div className={fullScreen ? "loading-overlay" : "loader-container"}>
        <div className={`${fullScreen ? "loading-overlay-content" : ""}`}>
          <div
            className={`${sizeMap[size]} bg-primary rounded-full spinner-glow`}
          />
          {text && (
            <span
              className={`${fullScreen ? "loading-text" : "text-xs text-gray-500"}`}
            >
              {text}
            </span>
          )}
        </div>
      </div>
    );
  }

  // Default fallback
  return (
    <div className={fullScreen ? "loading-overlay" : "loader-container"}>
      <div className={`${fullScreen ? "loading-overlay-content" : ""}`}>
        <Loader2 className={`${sizeMap[size]} animate-spin text-primary`} />
        {text && (
          <span
            className={`${fullScreen ? "loading-text" : "text-xs text-gray-500"}`}
          >
            {text}
          </span>
        )}
      </div>
    </div>
  );
};

// Inline loading spinner (compact)
export const InlineSpinner = ({ size = "sm" }) => {
  const sizeMap = { sm: "w-4 h-4", md: "w-6 h-6", lg: "w-8 h-8" };
  return (
    <Loader2 className={`${sizeMap[size]} animate-spin text-primary inline`} />
  );
};

// Button loading spinner
export const ButtonSpinner = ({
  loading = false,
  children,
  disabled = false,
  ...props
}) => {
  return (
    <button
      disabled={loading || disabled}
      className="flex items-center justify-center gap-2"
      {...props}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  );
};

// Loading Card
export const LoadingCard = ({ size = "md" }) => {
  return (
    <div className="glass p-8 rounded-2xl border-white/5 flex flex-col items-center justify-center min-h-64 gap-4">
      <LoadingSpinner type="ring" size={size} text="" />
      <p className="text-sm text-gray-500 font-medium">Loading...</p>
    </div>
  );
};

// Loading Skeleton
export const LoadingSkeleton = ({ rows = 3, columns = 1 }) => {
  return (
    <div className="space-y-4">
      {[...Array(rows)].map((_, i) => (
        <div
          key={i}
          className="grid gap-3"
          style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
        >
          {[...Array(columns)].map((_, j) => (
            <div
              key={j}
              className="h-12 bg-white/5 rounded-lg animate-pulse border border-white/5"
            />
          ))}
        </div>
      ))}
    </div>
  );
};

export default LoadingSpinner;
