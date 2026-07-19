"use client";
import { useState } from "react";
import { History, LogOut, Trash2 } from "lucide-react";

import { AppUser, HistoryEntry } from "@/app/lib/api";
import { Button } from "@/app/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";
import { ProfileModal } from "@/app/components/dashboard/profile-modal";

function getInitials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "U";
}

export function Sidebar({
  user,
  history,
  activeId,
  onHistorySelect,
  onHistoryDelete,
  onLogout,
  onUserUpdate,
}: {
  user: AppUser;
  history: HistoryEntry[];
  activeId: number | null;
  onHistorySelect: (item: HistoryEntry) => void;
  onHistoryDelete: (id: number) => void;
  onLogout: () => void;
  onUserUpdate: (user: AppUser) => void;
}) {
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex h-full flex-col border-r border-border bg-card">
        <div className="flex items-center gap-2 border-b border-border p-4">
          <History className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-foreground">History</h2>
        </div>

        <div className="flex-grow overflow-y-auto p-2">
          {history.length === 0 && (
            <p className="px-2 py-6 text-center text-sm text-muted-foreground">
              No summaries yet.
            </p>
          )}
          {history.map((item) => (
            <div
              key={item.id}
              onClick={() => onHistorySelect(item)}
              className={`group flex cursor-pointer items-center justify-between gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
                activeId === item.id
                  ? "bg-primary/15 text-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <p className="truncate">{item.query}</p>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onHistoryDelete(item.id);
                    }}
                    className="shrink-0 rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Delete</TooltipContent>
              </Tooltip>
            </div>
          ))}
        </div>

        <div className="space-y-2 border-t border-border p-4">
          <button
            onClick={() => setIsProfileOpen(true)}
            className="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left transition-colors hover:bg-muted"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-semibold text-primary">
              {getInitials(user.name)}
            </span>
            <span className="truncate text-sm font-medium text-foreground">
              {user.name || "Profile"}
            </span>
          </button>
          <Button variant="outline" onClick={onLogout} className="w-full justify-center">
            <LogOut className="h-4 w-4" /> Logout
          </Button>
        </div>
      </div>

      <ProfileModal
        isOpen={isProfileOpen}
        setIsOpen={setIsProfileOpen}
        user={user}
        onUserUpdate={onUserUpdate}
      />
    </TooltipProvider>
  );
}
