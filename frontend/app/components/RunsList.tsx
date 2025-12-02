"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RunsTable } from "@/components/RunsTable";

interface Run {
  id: string;
  status: string;
  created_at: string;
  notes: string;
  brands: { id: number; name: string }[];
  prompts: { id: number; text: string }[];
}

export default function RunsList({ refreshKey }: { refreshKey: number }) {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRuns = async () => {
    try {
      const res = await fetch("/api/runs");
      if (res.ok) {
        const data = await res.json();
        setRuns(data);
      }
    } catch (error) {
      console.error("Failed to fetch runs", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [refreshKey]);

  // Poll for updates if there are pending runs
  useEffect(() => {
    const interval = setInterval(() => {
      const hasPending = runs.some(r => r.status === 'pending' || r.status === 'running');
      if (hasPending) {
        fetchRuns();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [runs]);

  if (loading && runs.length === 0) {
    return <div className="text-center mt-8">Loading runs...</div>;
  }

  return (
    <Card className="w-full h-full">
      <CardHeader>
        <CardTitle>Past Runs</CardTitle>
      </CardHeader>
      <CardContent>
        <RunsTable runs={runs} />
      </CardContent>
    </Card>
  );
}
