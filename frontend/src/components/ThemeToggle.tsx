"use client";

import React, { useEffect, useState } from "react";
import { useTheme } from "./ThemeProvider";
import { Sun, Moon, Laptop } from "lucide-react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="h-7 w-20 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] animate-pulse" />
    );
  }

  return (
    <div
      role="radiogroup"
      aria-label="Theme mode"
      className="inline-flex items-center p-0.5 rounded-md border border-[var(--border)] bg-[var(--surface-secondary)]"
    >
      <button
        type="button"
        role="radio"
        aria-checked={theme === "light"}
        aria-label="Light theme"
        title="Light theme"
        onClick={() => setTheme("light")}
        className={`px-1.5 py-1 rounded-[4px] text-[11px] font-medium transition-colors flex items-center gap-1 ${
          theme === "light"
            ? "bg-[var(--surface)] text-[var(--fg)] shadow-xs border border-[var(--border)]"
            : "text-[var(--muted)] hover:text-[var(--fg)]"
        }`}
      >
        <Sun className="w-3 h-3" />
        <span className="sr-only sm:not-sr-only text-[10px]">Light</span>
      </button>

      <button
        type="button"
        role="radio"
        aria-checked={theme === "system"}
        aria-label="System theme"
        title="System theme"
        onClick={() => setTheme("system")}
        className={`px-1.5 py-1 rounded-[4px] text-[11px] font-medium transition-colors flex items-center gap-1 ${
          theme === "system"
            ? "bg-[var(--surface)] text-[var(--fg)] shadow-xs border border-[var(--border)]"
            : "text-[var(--muted)] hover:text-[var(--fg)]"
        }`}
      >
        <Laptop className="w-3 h-3" />
        <span className="sr-only sm:not-sr-only text-[10px]">Auto</span>
      </button>

      <button
        type="button"
        role="radio"
        aria-checked={theme === "dark"}
        aria-label="Dark theme"
        title="Dark theme"
        onClick={() => setTheme("dark")}
        className={`px-1.5 py-1 rounded-[4px] text-[11px] font-medium transition-colors flex items-center gap-1 ${
          theme === "dark"
            ? "bg-[var(--surface)] text-[var(--fg)] shadow-xs border border-[var(--border)]"
            : "text-[var(--muted)] hover:text-[var(--fg)]"
        }`}
      >
        <Moon className="w-3 h-3" />
        <span className="sr-only sm:not-sr-only text-[10px]">Dark</span>
      </button>
    </div>
  );
}
