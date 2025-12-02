"use client";

import { useState } from "react";
import CreateRunForm from "./components/CreateRunForm";
import RunsList from "./components/RunsList";
import { ModeToggle } from "@/components/mode-toggle";

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRunCreated = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="container mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white">
              AI Visibility Platform
            </h1>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Track brand visibility across LLM responses.
            </p>
          </div>
          <ModeToggle />
        </div>
        <div className="flex flex-col lg:flex-row gap-8 items-start">
          <div className="w-full lg:w-[30%]">
            <CreateRunForm onRunCreated={handleRunCreated} />
          </div>
          <div className="w-full lg:w-[70%]">
            <RunsList refreshKey={refreshKey} />
          </div>
        </div>
      </div>
    </div>
  );
}
