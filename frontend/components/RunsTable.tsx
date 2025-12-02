"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";

interface Run {
  id: string;
  created_at: string;
  status: string;
  brands: { name: string }[];
  prompts: { text: string }[];
}

interface RunsTableProps {
  runs: Run[];
}

export function RunsTable({ runs }: RunsTableProps) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Date</TableHead>
            <TableHead className="text-center">Status</TableHead>
            <TableHead className="text-center">Brands</TableHead>
            <TableHead className="text-center">Prompts</TableHead>
            <TableHead className="text-center">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {runs.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="h-24 text-center">
                No runs found.
              </TableCell>
            </TableRow>
          ) : (
            runs.map((run) => (
              <TableRow key={run.id}>
                <TableCell className="font-medium font-mono text-xs">
                  {run.id.slice(0, 8)}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(run.created_at).toLocaleString()}
                </TableCell>
                <TableCell className="text-center">
                  <Badge
                    className={
                      run.status === "completed"
                        ? "bg-green-500 hover:bg-green-600"
                        : run.status === "failed"
                        ? "bg-red-500 hover:bg-red-600"
                        : "bg-yellow-500 hover:bg-yellow-600"
                    }
                  >
                    {run.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-center">{run.brands.length}</TableCell>
                <TableCell className="text-center">{run.prompts.length}</TableCell>
                <TableCell className="text-center">
                  <Button asChild variant="outline" size="sm">
                    <Link href={`/runs/${run.id}`}>View Details</Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
