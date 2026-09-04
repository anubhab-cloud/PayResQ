import React from 'react';

interface PayResQLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showTagline?: boolean;
  textColor?: string;
}

export const PayResQLogo: React.FC<PayResQLogoProps> = ({
  className = '',
  size = 'md',
  showTagline = true,
  textColor = 'text-white',
}) => {
  const iconSizes = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-10 w-10',
  };

  const textSizes = {
    sm: 'text-base',
    md: 'text-xl',
    lg: 'text-2xl',
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Geometric Stylized Blue Arrow/Ribbon Logo Emblem */}
      <svg
        viewBox="0 0 100 100"
        className={`${iconSizes[size]} shrink-0 text-blue-500`}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M20 85L55 15H80L45 85H20Z"
          fill="url(#logo-grad-1)"
        />
        <path
          d="M45 45L75 15H92L62 45H45Z"
          fill="url(#logo-grad-2)"
        />
        <defs>
          <linearGradient id="logo-grad-1" x1="20" y1="85" x2="80" y2="15" gradientUnits="userSpaceOnUse">
            <stop stopColor="#2563EB" />
            <stop offset="1" stopColor="#3B82F6" />
          </linearGradient>
          <linearGradient id="logo-grad-2" x1="45" y1="45" x2="92" y2="15" gradientUnits="userSpaceOnUse">
            <stop stopColor="#60A5FA" />
            <stop offset="1" stopColor="#93C5FD" />
          </linearGradient>
        </defs>
      </svg>

      <div>
        <div className={`font-black tracking-tight leading-none ${textSizes[size]} ${textColor}`}>
          PayResQ
        </div>
        {showTagline && (
          <p className="text-[9px] font-medium tracking-wider text-slate-400 mt-0.5 uppercase">
            Recover. Retain. Grow.
          </p>
        )}
      </div>
    </div>
  );
};
