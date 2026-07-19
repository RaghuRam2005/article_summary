"use client";
import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";

import { AppUser, HistoryEntry, deleteHistoryItem, listHistory } from "@/app/lib/api";
import { Sidebar } from "@/app/components/dashboard/sidebar";
import { MainContent } from "@/app/components/dashboard/main-content";

export function HomePage({
  user,
  onLogout,
  onUserUpdate,
}: {
  user: AppUser;
  onLogout: () => void;
  onUserUpdate: (user: AppUser) => void;
}) {
  const [activeResult, setActiveResult] = useState<HistoryEntry | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    listHistory().then(setHistory).catch(() => setHistory([]));
  }, []);

  const handleHistorySelect = (item: HistoryEntry) => {
    setActiveResult(item);
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  };

  const handleHistoryCreated = (item: HistoryEntry) => {
    setHistory((prev) => [item, ...prev]);
  };

  const handleHistoryDelete = async (id: number) => {
    setHistory((prev) => prev.filter((item) => item.id !== id));
    if (activeResult?.id === id) setActiveResult(null);
    try {
      await deleteHistoryItem(id);
    } catch {
      listHistory().then(setHistory).catch(() => {});
    }
  };

  return (
    <div className="flex h-screen w-screen bg-background text-foreground">
      <div
        className={`fixed z-40 h-full w-64 transform transition-transform md:relative md:w-72 md:translate-x-0 lg:w-80 ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <Sidebar
          user={user}
          history={history}
          activeId={activeResult?.id ?? null}
          onHistorySelect={handleHistorySelect}
          onHistoryDelete={handleHistoryDelete}
          onLogout={onLogout}
          onUserUpdate={onUserUpdate}
        />
      </div>

      <main className="relative flex flex-1 flex-col">
        <div className="absolute left-4 top-4 z-50 md:hidden">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="rounded-md border border-border bg-card p-2 text-foreground"
          >
            {isSidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
        <div className="relative flex-1">
          <MainContent
            user={user}
            activeResult={activeResult}
            setActiveResult={setActiveResult}
            onHistoryCreated={handleHistoryCreated}
          />
        </div>
      </main>
    </div>
  );
}
