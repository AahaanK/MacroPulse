import React from "react";

/**
 * MacroPulse mark: a quiet baseline, the release-day marker (orange) and the market's
 * cumulative reaction after it — an event study drawn in three strokes.
 */
export const LogoMark: React.FC<{ size?: number; tone?: "light" | "dark"; className?: string }> = ({
  size = 28,
  tone = "light",
  className,
}) => {
  // tone="light": used on light surfaces (deep navy tile). tone="dark": on deep navy (navy tile).
  const tile = tone === "light" ? "#1B2632" : "#2C3B4D";
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden
    >
      <rect width="32" height="32" rx="7" fill={tile} />
      <rect x="13.25" y="6" width="2.5" height="20" rx="1.25" fill="#FFB162" />
      <path
        d="M6 19.5H14.5L18.25 14.25L21 16L26 9.5"
        stroke="#EEE9DF"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

export const Logo: React.FC<{ tone?: "light" | "dark"; size?: number; className?: string; showWordmark?: boolean }> = ({
  tone = "light",
  size = 28,
  className,
  showWordmark = true,
}) => (
  <span className={`inline-flex items-center gap-2.5 ${className ?? ""}`}>
    <LogoMark size={size} tone={tone} />
    {showWordmark && (
      <span
        className={`font-semibold tracking-[-0.015em] ${
          tone === "light" ? "text-abyssal" : "text-palladian"
        }`}
        style={{ fontSize: size * 0.6 }}
      >
        MacroPulse
      </span>
    )}
  </span>
);
