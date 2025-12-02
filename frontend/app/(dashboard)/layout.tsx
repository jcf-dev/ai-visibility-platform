"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ModeToggle } from "@/components/mode-toggle";
import CreateRunForm from "../components/CreateRunForm";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  const handleRunCreated = (newRun?: { id: string }) => {
    if (newRun && newRun.id) {
      router.push(`/runs/${newRun.id}`);
    }
  };

  return (
    <div className="min-h-screen">
      <div className="flex justify-between items-center mb-8">
        <div>
          <Link href="/">
            <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white cursor-pointer">
              AI Visibility Platform
            </h1>
          </Link>
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
          {children}
        </div>
      </div>
    </div>
  );
}
