"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { Skeleton } from "@/components/ui/skeleton";

interface RunDetail {
  id: string;
  status: string;
  created_at: string;
  notes: string;
  brands: { id: number; name: string }[];
  prompts: { id: number; text: string }[];
  responses: {
    id: number;
    prompt_text: string;
    model: string;
    latency_ms: number;
    raw_text: string;
    mentions: { brand_name: string; mentioned: boolean }[];
    error?: string;
  }[];
}

interface RunSummary {
  total_prompts: number;
  total_responses: number;
  metrics: {
    brand_name: string;
    total_prompts: number;
    mentions: number;
    visibility_score: number;
  }[];
}

export default function RunDetailsPage() {
  const params = useParams();
  const id = params.id as string;
  const [run, setRun] = useState<RunDetail | null>(null);
  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showResponses, setShowResponses] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [runRes, summaryRes] = await Promise.all([
        fetch(`/api/runs/${id}`),
        fetch(`/api/runs/${id}/summary`),
      ]);

      if (runRes.ok) {
        const runData = await runRes.json();
        setRun(runData);
      }
      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        setSummary(summaryData);
      }
    } catch (err) {
      console.error("Failed to fetch run data", err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      if (run?.status === "pending" || run?.status === "running") {
        fetchData();
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [fetchData, run?.status]);

  if (loading && !run) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-6 w-20" />
        </div>
        <div className="mb-8">
          <Skeleton className="h-8 w-40 mb-2" />
          <Skeleton className="h-4 w-full mb-6" />
          <div className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-32" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-40" />
            </div>
          </div>
        </div>
        <div className="flex justify-between items-center">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-24" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-40 w-full rounded-xl" />
          <Skeleton className="h-40 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (!run) {
    return <div className="p-8 text-center text-red-500">Run not found</div>;
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <Button variant="outline" asChild>
          <Link href="/">
            &larr; Back to Past Runs
          </Link>
        </Button>
        <Badge
          className={
            run.status === "completed"
              ? "bg-green-500 hover:bg-green-600"
              : run.status === "failed"
              ? "bg-red-500 hover:bg-red-600"
              : "bg-yellow-500 hover:bg-yellow-600"
          }
        >
          {run.status.toUpperCase()}
        </Badge>
      </div>

      <div className="mb-8">
        <div className="mb-4">
          <h2 className="text-2xl font-bold tracking-tight">Run Summary</h2>
          <p className="text-sm text-muted-foreground">
            {run.notes || "No notes provided."}
          </p>
        </div>
        <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-muted-foreground">Run ID</dt>
            <dd className="mt-1 text-sm text-foreground">{run.id}</dd>
          </div>
          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-muted-foreground">Created At</dt>
            <dd className="mt-1 text-sm text-foreground">
              {new Date(run.created_at).toLocaleString()}
            </dd>
          </div>
          {summary && (
            <div className="sm:col-span-2">
              <dt className="text-sm font-medium text-muted-foreground mb-2">Visibility Scores</dt>
              <dd className="text-sm text-foreground">
                <div className="border rounded-md divide-y">
                  {summary.metrics.map((metric) => (
                    <div key={metric.brand_name} className="px-4 py-3 flex items-center justify-between">
                      <span className="font-medium">{metric.brand_name}</span>
                      <span className="font-bold">{metric.visibility_score.toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </dd>
            </div>
          )}
        </dl>
      </div>

      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-xl font-bold text-foreground">Responses</h3>
        <button
          onClick={() => setShowResponses(!showResponses)}
          className="text-sm text-indigo-600 hover:text-indigo-500 font-medium"
        >
          {showResponses ? "Hide Details" : "Show Details"}
        </button>
      </div>

      {showResponses && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          {run.responses.map((response) => (
            <Card key={response.id}>
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {response.model}
                    </span>
                    <h4 className="text-md font-medium text-foreground mt-1">
                      {response.prompt_text}
                    </h4>
                  </div>
                  <span className="text-xs text-muted-foreground">{response.latency_ms.toFixed(0)}ms</span>
                </div>
                
                {response.error ? (
                  <div className="mt-2 p-3 bg-destructive/10 text-destructive rounded text-sm">
                    Error: {response.error}
                  </div>
                ) : (
                  <div className="mt-2 text-sm text-foreground whitespace-pre-wrap bg-muted p-3 rounded">
                    {response.raw_text}
                  </div>
                )}

                <div className="mt-4 flex gap-2">
                  {response.mentions.map((m) => (
                    <Badge
                      key={m.brand_name}
                      variant={m.mentioned ? "default" : "secondary"}
                    >
                      {m.brand_name}: {m.mentioned ? "Yes" : "No"}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </motion.div>
      )}
    </div>
  );
}

