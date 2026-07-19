import { Sparkles, ArrowRight } from "lucide-react";

import { Button } from "@/app/components/ui/button";
import { GridBackground } from "@/app/components/ui/grid-background";

type Page = "signup" | "login" | "home";

export function LandingPage({ onNavigate }: { onNavigate: (page: Page) => void }) {
  return (
    <div className="relative flex min-h-screen w-full flex-col items-center justify-center overflow-hidden bg-background px-4">
      <GridBackground />

      <div className="absolute right-4 top-4 z-10 flex gap-2 sm:right-6 sm:top-6">
        <Button variant="ghost" onClick={() => onNavigate("login")}>
          Log in
        </Button>
        <Button onClick={() => onNavigate("signup")}>Sign up</Button>
      </div>

      <div className="relative z-10 flex max-w-2xl flex-col items-center text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
          <Sparkles className="h-3.5 w-3.5 text-primary" />
          AI-powered summaries
        </div>

        <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-6xl">
          Summarize anything, instantly
        </h1>
        <p className="mt-4 max-w-lg text-balance text-lg text-muted-foreground">
          Paste a keyword, a URL, or raw text — get a clear, concise summary in seconds.
          Log in to keep your history synced everywhere.
        </p>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Button size="lg" onClick={() => onNavigate("signup")}>
            Get started <ArrowRight className="h-4 w-4" />
          </Button>
          <Button size="lg" variant="outline" onClick={() => onNavigate("login")}>
            I already have an account
          </Button>
        </div>
      </div>
    </div>
  );
}
