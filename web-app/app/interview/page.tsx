'use client';

import { useRef, useState } from 'react';

interface AnalysisResult {
  transcription: string;
  fillerWordsPerMinute: number;
  wordsPerMinute: number;
  clarity: number;
  starStructure: {
    hasSituation: boolean;
    hasTask: boolean;
    hasAction: boolean;
    hasResult: boolean;
  };
}

const QUESTIONS = [
  'Tell me about a time you led a cross-functional team to achieve a challenging goal.',
  'Describe a situation where you had to make a difficult trade-off decision.',
  'Walk me through how you would design a feature for users with accessibility needs.',
  'Tell me about a time you failed. What did you learn?',
  'How would you prioritize features when everything feels urgent?',
];

export default function InterviewPracticePage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState('');

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm;codecs=vp8,opus',
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        await analyzeRecording(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setAnalysis(null);
      setIsRecording(true);
      setCurrentQuestion(QUESTIONS[Math.floor(Math.random() * QUESTIONS.length)]);
    } catch (error) {
      console.error('Error accessing camera/microphone:', error);
      alert('Please allow camera and microphone access to practice interviews.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const analyzeRecording = async (blob: Blob) => {
    setIsAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('audio', blob, 'interview.webm');

      const response = await fetch('/api/analyze-interview', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const result = (await response.json()) as AnalysisResult & { transcription: string };
      setAnalysis(result);
    } catch (error) {
      console.error('Error analyzing recording:', error);
      alert('Failed to analyze your interview. See console for details.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <main className="min-h-screen p-8 md:p-12 bg-gray-50">
      <div className="max-w-4xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl md:text-4xl font-bold">Interview Practice</h1>
          <p className="text-gray-600 mt-2">
            Record behavioral answers, then get instant metrics on pace, fillers, clarity, and STAR
            coverage.
          </p>
        </header>

        {!isRecording && !analysis && !isAnalyzing && (
          <section className="bg-white p-8 rounded-lg shadow-sm space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-2">Practice behavioral interviews</h2>
              <p className="text-gray-600">
                You&apos;ll receive a random question. Answer using the STAR framework (Situation, Task,
                Action, Result) while staying concise and present.
              </p>
            </div>

            <button
              onClick={startRecording}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Start Recording
            </button>
          </section>
        )}

        {isRecording && (
          <section className="bg-white p-8 rounded-lg shadow-sm space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Recording…</h2>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
                Live
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 p-4 rounded">
              <p className="font-semibold text-blue-900">Question:</p>
              <p className="text-blue-800 mt-2">{currentQuestion}</p>
            </div>

            <video ref={videoRef} autoPlay muted className="w-full rounded border" />

            <div className="bg-gray-50 p-4 rounded border text-sm space-y-2">
              <p className="font-semibold">STAR reminder</p>
              <p>Situation · Task · Action · Result. Spend ~20% on context, 70% on actions, 10% on outcome.</p>
            </div>

            <button
              onClick={stopRecording}
              className="w-full bg-red-600 text-white py-3 rounded-lg font-semibold hover:bg-red-700 transition"
            >
              Stop &amp; Analyze
            </button>
          </section>
        )}

        {isAnalyzing && (
          <section className="bg-white p-8 rounded-lg shadow-sm text-center">
            <div className="mx-auto h-12 w-12 border-3 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
            <p className="mt-4 text-gray-600">Transcribing and analyzing your answer…</p>
          </section>
        )}

        {analysis && !isRecording && (
          <section className="bg-white p-8 rounded-lg shadow-sm space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <MetricCard
                label="Words per minute"
                value={analysis.wordsPerMinute.toString()}
                message={
                  analysis.wordsPerMinute >= 130 && analysis.wordsPerMinute <= 160
                    ? 'Great pace'
                    : 'Adjust your pacing'
                }
              />
              <MetricCard
                label="Filler words / min"
                value={analysis.fillerWordsPerMinute.toFixed(1)}
                message={analysis.fillerWordsPerMinute < 2 ? 'Excellent control' : 'Trim the filler words'}
              />
              <MetricCard
                label="Words per sentence"
                value={analysis.clarity.toFixed(1)}
                message={analysis.clarity >= 15 && analysis.clarity <= 25 ? 'Clear and concise' : 'Tighten structure'}
              />
              <MetricCard
                label="STAR elements"
                value={`${Object.values(analysis.starStructure).filter(Boolean).length}/4`}
                message={
                  Object.values(analysis.starStructure).every(Boolean)
                    ? 'Complete story arc'
                    : 'Fill in missing pieces'
                }
              />
            </div>

            <div>
              <h3 className="font-semibold mb-2">STAR checklist</h3>
              <ul className="space-y-2 text-sm text-gray-700">
                <StarItem label="Situation" checked={analysis.starStructure.hasSituation} />
                <StarItem label="Task" checked={analysis.starStructure.hasTask} />
                <StarItem label="Action" checked={analysis.starStructure.hasAction} />
                <StarItem label="Result" checked={analysis.starStructure.hasResult} />
              </ul>
            </div>

            <div className="bg-gray-50 p-4 rounded border">
              <h3 className="font-semibold mb-2">Transcription</h3>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{analysis.transcription}</p>
            </div>

            <div className="flex flex-col md:flex-row gap-4">
              <button
                onClick={() => {
                  setAnalysis(null);
                  setCurrentQuestion('');
                }}
                className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                Practice Again
              </button>
              <button
                onClick={() => alert('TODO: Save this session to Supabase')}
                className="flex-1 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition"
              >
                Save Session
              </button>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

function MetricCard({ value, label, message }: { value: string; label: string; message: string }) {
  return (
    <div className="p-4 bg-gray-50 border rounded">
      <p className="text-sm text-gray-500 uppercase">{label}</p>
      <p className="text-3xl font-bold text-blue-600 mt-1">{value}</p>
      <p className="text-xs text-gray-600 mt-2">{message}</p>
    </div>
  );
}

function StarItem({ label, checked }: { label: string; checked: boolean }) {
  return (
    <li className="flex items-center gap-2">
      <span className={checked ? 'text-green-600' : 'text-red-500'}>{checked ? '✅' : '❌'}</span>
      <span>{label}</span>
    </li>
  );
}
