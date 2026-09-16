"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Building2,
  ListTodo,
  BarChart3,
  ShieldCheck,
  Menu,
  X,
  ArrowRight,
} from "lucide-react";
import Image from "next/image";
import { ThemeToggle } from "./ThemeToggle";
import { useTheme } from "./ThemeProvider";

interface ShellProps {
  children: React.ReactNode;
}

export function Shell({ children }: ShellProps) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  const navItems = [
    {
      label: "Overview",
      href: "/",
      icon: LayoutDashboard,
      active: pathname === "/",
    },
    {
      label: "CSE Assessments",
      href: "/cses",
      icon: Building2,
      active: pathname.startsWith("/cses"),
    },
    {
      label: "Review Queue",
      href: "/review-queue",
      icon: ListTodo,
      active: pathname.startsWith("/review-queue"),
    },
    {
      label: "Analytics",
      href: "/analytics",
      icon: BarChart3,
      active: pathname.startsWith("/analytics"),
    },
    {
      label: "Data Quality",
      href: "/data-quality",
      icon: ShieldCheck,
      active: pathname.startsWith("/data-quality"),
    },
  ];

  const currentLogoSrc = mounted
    ? resolvedTheme === "dark"
      ? "/sentra_whiteonblack.png"
      : "/sentra_blackonwhite.png"
    : "/sentra_whiteonblack.png";

  return (
    <div className="h-screen bg-[var(--bg)] text-[var(--fg)] flex flex-col font-sans overflow-hidden">
      {/* Top Header - Restrained, Flush, Nearly Invisible Chrome */}
      <header className="h-15 border-b border-[var(--border)] bg-[var(--surface)] px-4 sm:px-6 flex items-center justify-between sticky top-0 z-40 transition-colors shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-1.5 rounded-md text-[var(--muted)] hover:text-[var(--fg)] hover:bg-[var(--surface-secondary)] transition cursor-pointer"
            aria-label="Toggle navigation"
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>

          <Link href="/" className="flex items-center py-1">
            <Image
              src={currentLogoSrc}
              alt="SENTRA"
              width={160}
              height={52}
              className="h-9 sm:h-10 w-auto object-contain transition-opacity duration-150"
              priority
            />
          </Link>
        </div>

        {/* Status indicator & Theme Toggle */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-2 py-1 rounded-md text-[11px] font-mono text-[var(--muted)] bg-[var(--surface-secondary)] border border-[var(--border)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-low-dot)]" />
            <span>Local · Offline</span>
          </div>

          <ThemeToggle />
        </div>
      </header>

      {/* Main Workspace Frame */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Desktop Fixed Quiet Surface */}
        <aside className="w-60 border-r border-[var(--border)] bg-[var(--surface)] hidden md:flex flex-col justify-between shrink-0 transition-colors h-full overflow-y-auto">
          <div className="p-3 space-y-1">
            <nav className="space-y-0.5" aria-label="Main Navigation">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${item.active
                      ? "bg-[var(--surface-secondary)] text-[var(--fg)] font-semibold"
                      : "text-[var(--muted)] hover:text-[var(--fg)] hover:bg-[var(--surface-secondary)]"
                      }`}
                  >
                    <Icon className="w-4 h-4 shrink-0 text-[var(--muted)]" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            {/* Quiet Primary Demo Shortcut */}
            <div className="pt-6 px-1">
              <Link
                href="/cses/CSE-011"
                className="block p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] hover:border-[var(--muted)] transition text-xs space-y-1 group"
              >
                <div className="flex items-center justify-between text-[11px] font-medium text-[var(--fg)]">
                  <span>Primary Demo: CSE-011</span>
                  <ArrowRight className="w-3 h-3 text-[var(--muted)] group-hover:translate-x-0.5 transition-transform" />
                </div>
                <p className="text-[10px] text-[var(--muted)] leading-relaxed">
                  Systemic investigation effort gap with multi-phase corroboration.
                </p>
              </Link>
            </div>
          </div>
        </aside>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div
            className="fixed inset-0 z-30 bg-black/40 backdrop-blur-xs md:hidden"
            onClick={() => setMobileMenuOpen(false)}
          >
            <div
              className="w-64 bg-[var(--surface)] border-r border-[var(--border)] h-full p-4 space-y-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="pb-3 border-b border-[var(--border)]">
                <Link
                  href="/"
                  className="flex items-center"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Image
                    src={currentLogoSrc}
                    alt="SENTRA"
                    width={140}
                    height={46}
                    className="h-8.5 w-auto object-contain"
                  />
                </Link>
              </div>
              <span className="text-[10px] font-mono text-[var(--subtle)] uppercase tracking-wider block">
                Supervisory Navigation
              </span>
              <nav className="space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${item.active
                        ? "bg-[var(--surface-secondary)] text-[var(--fg)] font-semibold"
                        : "text-[var(--muted)] hover:text-[var(--fg)] hover:bg-[var(--surface-secondary)]"
                        }`}
                    >
                      <Icon className="w-4 h-4 shrink-0 text-[var(--muted)]" />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </nav>

              <div className="pt-4 border-t border-[var(--border)]">
                <Link
                  href="/cses/CSE-011"
                  className="block p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] text-xs"
                >
                  <span className="font-semibold text-[var(--fg)] block">
                    Inspect CSE-011
                  </span>
                  <span className="text-[11px] text-[var(--muted)]">
                    Primary demonstration entity
                  </span>
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Page Content Viewport */}
        <main className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 pb-8 pt-0 bg-[var(--bg)] transition-colors">
          <div className="max-w-6xl mx-auto pt-4 sm:pt-6 lg:pt-8 space-y-6 animate-page-enter">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
