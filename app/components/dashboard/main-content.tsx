"use client";
import { useState } from "react";
import { Loader2, Send } from "lucide-react";

import { AppUser, BackendUrl, HistoryEntry, createHistory } from "@/app/lib/api";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { Textarea } from "@/app/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs";

type HistoryItem = HistoryEntry;

export function MainContent({
  user,
  activeResult,
  setActiveResult,
  onHistoryCreated,
}: {
  user: AppUser;
  activeResult: HistoryItem | null;
  setActiveResult: (result: HistoryItem | null) => void;
  onHistoryCreated: (item: HistoryItem) => void;
}) {
  const [inputType, setInputType] = useState<"keyword" | "url" | "content">("keyword");
  const [keyword, setKeyword] = useState("");
  const [url, setUrl] = useState("");
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSummarize = async () => {
    let query = "";
    if (inputType === "keyword") query = keyword;
    else if (inputType === "url") query = url;
    else query = content;

    if (!query.trim()) return;

    setIsLoading(true);

    const payload: Record<string, string> = {};
    if (inputType === "keyword") payload.keyword = query;
    else if (inputType === "url") payload.url = query;
    else payload.content = query;

    let summary = "";
    try {
      const res = await fetch(`${BackendUrl}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      summary = data.status === "success" && data.summary ? data.summary : "Failed to generate summary.";
    } catch {
      summary = "Error connecting to backend.";
    }

    if (user) {
      const created = await createHistory(query, inputType, summary);
      onHistoryCreated(created);
      setActiveResult(created);
    } else {
      setActiveResult({ id: 0, query, type: inputType, response: summary, timestamp: new Date().toISOString() });
    }

    setIsLoading(false);
    setKeyword("");
    setUrl("");
    setContent("");
  };

  if (activeResult) {
    return (
      <div className="h-full overflow-y-auto p-6 md:p-10">
        <Button variant="outline" onClick={() => setActiveResult(null)} className="mb-6">
          New Summary
        </Button>
        <div className="mx-auto max-w-3xl space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-muted-foreground">
                Your query <span className="text-foreground">({activeResult.type})</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap break-words text-sm text-muted-foreground">
                {activeResult.query}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-primary">Generated summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap break-words leading-relaxed text-foreground">
                {activeResult.response}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col justify-center p-6 md:p-10">
      <div className="mx-auto w-full max-w-2xl">
        <h1 className="mb-8 text-center text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
          Summarize Anything
        </h1>
        <Tabs value={inputType} onValueChange={(v) => setInputType(v as typeof inputType)}>
          <div className="flex justify-center">
            <TabsList>
              <TabsTrigger value="keyword">Keyword</TabsTrigger>
              <TabsTrigger value="url">URL</TabsTrigger>
              <TabsTrigger value="content">Content</TabsTrigger>
            </TabsList>
          </div>
          <TabsContent value="keyword">
            <Input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Enter a keyword or topic"
            />
          </TabsContent>
          <TabsContent value="url">
            <Input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
            />
          </TabsContent>
          <TabsContent value="content">
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste your text here..."
              className="h-48"
            />
          </TabsContent>
        </Tabs>
        <div className="mt-8 flex justify-center">
          <Button size="lg" onClick={handleSummarize} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Processing...
              </>
            ) : (
              <>
                <Send className="h-4 w-4" /> Summarize
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
