"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

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
    return <div className="p-8 text-center">Loading...</div>;
  }

  if (!run) {
    return <div className="p-8 text-center text-red-500">Run not found</div>;
  }

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <Link href="/" className="text-indigo-600 hover:text-indigo-500">
            &larr; Back to Dashboard
          </Link>
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              run.status === "completed"
                ? "bg-green-100 text-green-800"
                : run.status === "failed"
                ? "bg-red-100 text-red-800"
                : "bg-yellow-100 text-yellow-800"
            }`}
          >
            {run.status.toUpperCase()}
          </span>
        </div>

        <div className="bg-white dark:bg-zinc-900 shadow overflow-hidden sm:rounded-lg mb-8">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
              Run Summary
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
              {run.notes || "No notes provided."}
            </p>
          </div>
          <div className="border-t border-gray-200 dark:border-zinc-700 px-4 py-5 sm:p-0">
            <dl className="sm:divide-y sm:divide-gray-200 dark:sm:divide-zinc-700">
              <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Run ID</dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2">{run.id}</dd>
              </div>
              <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Created At</dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2">
                  {new Date(run.created_at).toLocaleString()}
                </dd>
              </div>
              {summary && (
                <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Visibility Scores</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2">
                    <ul className="border border-gray-200 dark:border-zinc-700 rounded-md divide-y divide-gray-200 dark:divide-zinc-700">
                      {summary.metrics.map((metric) => (
                        <li key={metric.brand_name} className="pl-3 pr-4 py-3 flex items-center justify-between text-sm">
                          <div className="w-0 flex-1 flex items-center">
                            <span className="font-medium truncate">{metric.brand_name}</span>
                          </div>
                          <div className="ml-4 flex-shrink-0 font-bold">
                            {metric.visibility_score.toFixed(1)}%
                          </div>
                        </li>
                      ))}
                    </ul>
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">Responses</h3>
          <button
            onClick={() => setShowResponses(!showResponses)}
            className="text-sm text-indigo-600 hover:text-indigo-500 font-medium"
          >
            {showResponses ? "Hide Details" : "Show Details"}
          </button>
        </div>

        {showResponses && (
          <div className="space-y-4">
            {run.responses.map((response) => (
              <div key={response.id} className="bg-white dark:bg-zinc-900 shadow sm:rounded-lg p-6">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                      {response.model}
                    </span>
                    <h4 className="text-md font-medium text-gray-900 dark:text-white mt-1">
                      {response.prompt_text}
                    </h4>
                  </div>
                  <span className="text-xs text-gray-400">{response.latency_ms.toFixed(0)}ms</span>
                </div>
                
                {response.error ? (
                  <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded text-sm">
                    Error: {response.error}
                  </div>
                ) : (
                  <div className="mt-2 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap bg-gray-50 dark:bg-zinc-800 p-3 rounded">
                    {response.raw_text}
                  </div>
                )}

                <div className="mt-4 flex gap-2">
                  {response.mentions.map((m) => (
                    <span
                      key={m.brand_name}
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        m.mentioned
                          ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                          : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                      }`}
                    >
                      {m.brand_name}: {m.mentioned ? "Yes" : "No"}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
