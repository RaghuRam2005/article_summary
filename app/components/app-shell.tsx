"use client";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { AppUser, getCurrentUser, logOut } from "@/app/lib/api";
import { LandingPage } from "@/app/components/landing-page";
import { SignUpForm } from "@/app/components/auth/signup-form";
import { LoginForm } from "@/app/components/auth/login-form";
import { HomePage } from "@/app/components/dashboard/home-page";

type Page = "signup" | "login" | "home";

export function AppShell() {
  const [page, setPage] = useState<Page>("home");
  const [user, setUser] = useState<AppUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .finally(() => setIsLoading(false));
  }, []);

  const handleNavigate = (newPage: Page) => setPage(newPage);

  const handleLogout = async () => {
    await logOut();
    setUser(null);
    setPage("home");
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen w-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (user) {
    return <HomePage user={user} onLogout={handleLogout} onUserUpdate={setUser} />;
  }

  if (page === "signup") {
    return <SignUpForm onNavigate={handleNavigate} onAuthSuccess={setUser} />;
  }

  if (page === "login") {
    return <LoginForm onNavigate={handleNavigate} onAuthSuccess={setUser} />;
  }

  return <LandingPage onNavigate={handleNavigate} />;
}
