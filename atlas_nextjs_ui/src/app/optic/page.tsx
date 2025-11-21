'use client';

import AppLayout from '@/components/layout/app-layout';
import { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { UploadCloud, RefreshCw } from 'lucide-react';

type VisionJob = {
  job_id: string;
  status: string;
  result?: Record<string, any>;
  error?: string | null;
};

export default function OpticPage() {
  const apiBase = useMemo(
    () => (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011').replace(/\/$/, ''),
    []
  );
  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<VisionJob | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`${apiBase}/atlas/senses/optic/upload`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error(`Upload failed (${res.status})`);
      const data = await res.json();
      setJob(data);
    } catch (e: any) {
      setError(e.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const refreshJob = async () => {
    if (!job?.job_id) return;
    try {
      const res = await fetch(`${apiBase}/atlas/senses/optic/jobs/${job.job_id}`);
      if (!res.ok) throw new Error(`Job fetch failed (${res.status})`);
      const data = await res.json();
      setJob(data);
    } catch (e: any) {
      setError(e.message || 'Job fetch failed');
    }
  };

  return (
    <AppLayout>
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Optic Nerve Ingestion</h2>
            <p className="text-muted-foreground">Upload visual context and follow the parsing job.</p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Upload</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <Button onClick={upload} disabled={!file || isUploading} className="flex items-center gap-2">
              {isUploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
              {isUploading ? 'Uploading...' : 'Upload & Process'}
            </Button>
            {error && <div className="text-sm text-red-400">{error}</div>}
          </CardContent>
        </Card>

        {job && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Job {job.job_id}
                <Badge variant="secondary" className="capitalize">
                  {job.status}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" size="sm" onClick={refreshJob} className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4" /> Refresh Status
              </Button>
              {job.result && Object.keys(job.result).length > 0 && (
                <pre className="bg-black/50 text-white text-xs p-3 rounded-lg overflow-x-auto">
                  {JSON.stringify(job.result, null, 2)}
                </pre>
              )}
              {job.error && <div className="text-sm text-red-400">{job.error}</div>}
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}
