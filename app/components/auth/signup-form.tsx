"use client";
import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";

import { AppUser, signUp } from "@/app/lib/api";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { Card, CardContent, CardHeader } from "@/app/components/ui/card";
import { GridBackground } from "@/app/components/ui/grid-background";

type Page = "signup" | "login" | "home";

export function SignUpForm({
  onNavigate,
  onAuthSuccess,
}: {
  onNavigate: (page: Page) => void;
  onAuthSuccess: (user: AppUser) => void;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const newUser = await signUp(name, email, password);
      onAuthSuccess(newUser);
      onNavigate("home");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred while signing up");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen w-full items-center justify-center bg-background px-4">
      <GridBackground />
      <Card className="relative z-10 w-full max-w-sm">
        <CardHeader>
          <div className="mb-2 flex items-center gap-2 text-primary">
            <Sparkles className="h-5 w-5" />
            <span className="text-sm font-semibold tracking-wide text-foreground">Summarize</span>
          </div>
          <h1 className="text-xl font-semibold">Create your account</h1>
          <p className="text-sm text-muted-foreground">
            Start summarizing articles, URLs, and text in seconds.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSignup} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="signup-name">Name</Label>
              <Input
                id="signup-name"
                required
                type="text"
                placeholder="Ada Lovelace"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="signup-email">Email</Label>
              <Input
                id="signup-email"
                required
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="signup-password">Password</Label>
              <Input
                id="signup-password"
                required
                type="password"
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            {error && (
              <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </div>
            )}

            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Creating account...
                </>
              ) : (
                "Sign Up"
              )}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <button
              onClick={() => onNavigate("login")}
              className="font-medium text-primary hover:underline"
            >
              Log in
            </button>
          </p>
        </CardContent>
      </Card>

      <button
        onClick={() => onNavigate("home")}
        className="absolute right-4 top-4 z-10 text-sm text-muted-foreground hover:text-foreground"
      >
        Back to home
      </button>
    </div>
  );
}
