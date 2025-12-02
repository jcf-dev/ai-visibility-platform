"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { MultiSelect, GroupedOption } from "@/components/ui/multi-select";

interface CreateRunFormProps {
  onRunCreated?: (run?: { id: string }) => void;
}

export default function CreateRunForm({ onRunCreated }: CreateRunFormProps) {
  const [models, setModels] = useState<Record<string, string[]>>({});
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [brands, setBrands] = useState<string>("");
  const [prompts, setPrompts] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/models")
      .then((res) => res.json())
      .then((data) => {
        setModels(data);
        // Select mock model by default if available
        if (data.mock && data.mock.length > 0) {
          setSelectedModels([data.mock[0]]);
        }
      })
      .catch((err) => console.error("Failed to fetch models", err));
  }, []);

  const modelOptions: GroupedOption[] = useMemo(() => {
    return Object.entries(models).map(([provider, modelList]) => ({
      label: provider.charAt(0).toUpperCase() + provider.slice(1),
      options: modelList.map((model) => ({
        label: model,
        value: model,
      })),
    }));
  }, [models]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const brandList = brands.split("\n").map((b) => b.trim()).filter((b) => b);
    const promptList = prompts.split("\n").map((p) => p.trim()).filter((p) => p);

    if (brandList.length === 0 || promptList.length === 0 || selectedModels.length === 0) {
      setError("Please fill in all fields (brands, prompts, and at least one model).");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          brands: brandList,
          prompts: promptList,
          models: selectedModels,
          notes: notes,
        }),
      });

      if (!res.ok) {
        throw new Error(`Error: ${res.statusText}`);
      }

      const data = await res.json();
      if (onRunCreated) {
        onRunCreated(data);
      }
      // Reset form or show success message?
      // For now, just keeping the form as is or maybe clearing it?
      // Let's clear the form for better UX
      setBrands("");
      setPrompts("");
      setNotes("");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Create New Run</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="brands">Brands (one per line)</Label>
            <Textarea
              id="brands"
              rows={3}
              value={brands}
              onChange={(e) => setBrands(e.target.value)}
              placeholder="Acme&#10;Globex"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="prompts">Prompts (one per line)</Label>
            <Textarea
              id="prompts"
              rows={3}
              value={prompts}
              onChange={(e) => setPrompts(e.target.value)}
              placeholder="Who is the best provider?&#10;Tell me about..."
            />
          </div>

          <div className="space-y-2">
            <Label>Models</Label>
            <MultiSelect
              options={modelOptions}
              selected={selectedModels}
              onChange={setSelectedModels}
              placeholder="Select models..."
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes (optional)</Label>
            <Textarea
              id="notes"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Experiment notes..."
            />
          </div>

          {error && (
            <div className="p-3 text-sm text-red-500 bg-red-50 dark:bg-red-900/20 rounded-md">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating Run..." : "Start Run"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

