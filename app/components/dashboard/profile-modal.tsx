"use client";
import { useState } from "react";
import { Loader2 } from "lucide-react";

import {
  AppUser,
  updateDisplayName,
  updateUserEmail,
  updateUserPassword,
} from "@/app/lib/api";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { Separator } from "@/app/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/app/components/ui/dialog";

export function ProfileModal({
  isOpen,
  setIsOpen,
  user,
  onUserUpdate,
}: {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
  user: AppUser;
  onUserUpdate: (user: AppUser) => void;
}) {
  const [displayName, setDisplayName] = useState(user.name || "");
  const [newEmail, setNewEmail] = useState(user.email || "");
  const [newPassword, setNewPassword] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleUpdate = async (updateType: "profile" | "email" | "password") => {
    setError("");
    setSuccess("");
    setIsLoading(true);

    try {
      if (updateType === "profile") {
        const updated = await updateDisplayName(displayName);
        onUserUpdate(updated);
        setSuccess("Display name updated successfully!");
      } else if (updateType === "email") {
        const updated = await updateUserEmail(newEmail, currentPassword);
        onUserUpdate(updated);
        setSuccess("Email updated successfully!");
      } else if (updateType === "password") {
        await updateUserPassword(newPassword, currentPassword);
        setSuccess("Password updated successfully!");
        setNewPassword("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred.");
    } finally {
      setIsLoading(false);
      setCurrentPassword("");
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Profile settings</DialogTitle>
          <DialogDescription>Update your name, email, or password.</DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {error && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          )}
          {success && (
            <div className="rounded-md border border-primary/30 bg-primary/10 px-3 py-2 text-sm text-primary">
              {success}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="profile-name">Display name</Label>
            <div className="flex gap-2">
              <Input
                id="profile-name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
              <Button
                onClick={() => handleUpdate("profile")}
                disabled={isLoading}
                variant="outline"
              >
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save"}
              </Button>
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Enter your current password to change your email or password.
            </p>
            <div className="space-y-2">
              <Label htmlFor="current-password">Current password</Label>
              <Input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
              />
            </div>

            <fieldset disabled={!currentPassword} className="space-y-4 disabled:opacity-50">
              <div className="space-y-2">
                <Label htmlFor="new-email">New email</Label>
                <div className="flex gap-2">
                  <Input
                    id="new-email"
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                  />
                  <Button
                    onClick={() => handleUpdate("email")}
                    disabled={isLoading || !currentPassword}
                    variant="outline"
                  >
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Update"}
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-password">New password</Label>
                <div className="flex gap-2">
                  <Input
                    id="new-password"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                  />
                  <Button
                    onClick={() => handleUpdate("password")}
                    disabled={isLoading || !currentPassword}
                    variant="outline"
                  >
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Update"}
                  </Button>
                </div>
              </div>
            </fieldset>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
