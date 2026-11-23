"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Cpu, LayoutDashboard, BookOpen, Swords, Flame, ShieldAlert, Sliders, Layers } from "lucide-react";
import { apiFetch } from "@/lib/api";

export function NavShell() {
  const pathname = usePathname();
  const [review, setReview] = useState<{
    total_core_xp: number;
    xp_to_next_review: number;
    review_triggered: boolean;
  } | null>(null);

  useEffect(() => {
    apiFetch("/api/overview")
      .then((d) => setReview(d.review))
      .catch(() => {});
  }, [pathname]);

  const navItems = [
    { href: "/", label: "1. Overview", icon: LayoutDashboard },
    { href: "/syllabus", label: "2. Core Syllabus", icon: BookOpen },
    { href: "/studio", label: "3. Interview Studio", icon: Swords },
    { href: "/sandboxes", label: "Sandboxes", icon: Sliders },
    { href: "/flashcards", label: "Flashcards", icon: Layers },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 font-mono text-sm font-bold tracking-tight text-white">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
              <Cpu className="h-4 w-4" />
            </span>
            <span>ML COMMAND CENTER</span>
            <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] font-normal text-zinc-400">
              PRIVATE
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : (pathname ? pathname.startsWith(item.href) : false);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                    active
                      ? "bg-zinc-800 text-white"
                      : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {review && (
            <>
              <div className="flex items-center gap-1.5 rounded-full border border-zinc-800 bg-zinc-900 px-3 py-1 font-mono text-xs text-amber-400">
                <Flame className="h-3.5 w-3.5" />
                <span>{review.total_core_xp} XP</span>
              </div>
              {review.review_triggered ? (
                <Link
                  href="/syllabus#review"
                  className="flex items-center gap-1.5 rounded-full border border-rose-500/50 bg-rose-500/15 px-3 py-1 font-mono text-xs text-rose-300 hover:bg-rose-500/25"
                >
                  <ShieldAlert className="h-3.5 w-3.5" />
                  150-XP Review Due
                </Link>
              ) : (
                <span className="hidden sm:inline font-mono text-xs text-zinc-500">
                  Next review in {review.xp_to_next_review} XP
                </span>
              )}
            </>
          )}
        </div>
      </div>
    </header>
  );
}
