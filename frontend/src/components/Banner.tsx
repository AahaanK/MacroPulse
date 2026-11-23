import React from "react";

interface BannerProps {
  message?: string | null;
  /** Optional trailing link or action, e.g. to the data sources page. */
  action?: React.ReactNode;
}

/** Thin notice strip shown above the app when the backend reports a data caveat. */
export const Banner: React.FC<BannerProps> = ({ message, action }) => {
  if (!message) return null;

  return (
    <div
      role="note"
      className="w-full shrink-0 border-b border-burning-flame/50 bg-burning-flame/20 dark:bg-burning-flame/10 dark:border-burning-flame/25 px-3 sm:px-5 py-1.5 flex flex-wrap items-center justify-between gap-x-4 gap-y-0.5 text-xs text-abyssal dark:text-palladian"
    >
      <span>
        <span className="font-medium">Note:</span> {message}
      </span>
      {action}
    </div>
  );
};
