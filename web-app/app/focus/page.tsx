'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

const SESSION_LENGTH = {
  pomodoro: 25 * 60,
  deep: 90 * 60,
} as const;

type SessionType = keyof typeof SESSION_LENGTH;

export default function FocusSessionPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [sessionType, setSessionType] = useState<SessionType>('pomodoro');
  const [isActive, setIsActive] = useState(false);
  const [sessionTime, setSessionTime] = useState(0);
  const [focusScore, setFocusScore] = useState(50);

  const duration = useMemo(() => SESSION_LENGTH[sessionType], [sessionType]);
  const progress = duration > 0 ? Math.min(100, (sessionTime / duration) * 100) : 0;

  useEffect(() => {
    if (!isActive) {
      return;
    }

    const interval = setInterval(() => {
      setSessionTime((prev) => {
        if (prev + 1 >= duration) {
          clearInterval(interval);
          stopSession();
          return duration;
        }
        return prev + 1;
      });

      // Placeholder focus score - swap with real CV model later.
      setFocusScore(() => Math.floor(40 + Math.random() * 60));
    }, 1000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive, duration]);

  useEffect(() => {
    return () => {
      stopMediaStream();
    };
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startSession = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setSessionTime(0);
      setIsActive(true);
    } catch (error) {
      console.error('Camera access denied:', error);
      alert('Please allow camera access to enable focus tracking.');
    }
  };

  const stopMediaStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  };

  const stopSession = () => {
    setIsActive(false);
    stopMediaStream();
  };

  return (
    <main className="min-h-screen p-8 md:p-12 bg-gray-50">
      <div className="max-w-4xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl md:text-4xl font-bold">Focus Session</h1>
          <p className="text-gray-600 mt-2">
            Choose your block length, start the camera, and work deeply while the app keeps soft tabs
            on your focus level.
          </p>
        </header>

        {!isActive ? (
          <section className="bg-white p-8 rounded-lg shadow-sm space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-4">Choose Session Type</h2>

              <div className="space-y-4">
                <label className="flex items-center p-4 border rounded hover:bg-gray-50 cursor-pointer">
                  <input
                    type="radio"
                    name="sessionType"
                    value="pomodoro"
                    checked={sessionType === 'pomodoro'}
                    onChange={() => setSessionType('pomodoro')}
                    className="mr-3"
                  />
                  <div>
                    <div className="font-semibold">Pomodoro (25 min)</div>
                    <div className="text-sm text-gray-600">Short burst to kickstart momentum.</div>
                  </div>
                </label>

                <label className="flex items-center p-4 border rounded hover:bg-gray-50 cursor-pointer">
                  <input
                    type="radio"
                    name="sessionType"
                    value="deep"
                    checked={sessionType === 'deep'}
                    onChange={() => setSessionType('deep')}
                    className="mr-3"
                  />
                  <div>
                    <div className="font-semibold">Deep Work (90 min)</div>
                    <div className="text-sm text-gray-600">Ride an ultradian rhythm cycle end-to-end.</div>
                  </div>
                </label>
              </div>
            </div>

            <button
              onClick={startSession}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Start Session
            </button>
          </section>
        ) : (
          <section className="bg-white p-8 rounded-lg shadow-sm space-y-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div>
                <p className="text-5xl font-bold">{formatTime(sessionTime)}</p>
                <p className="text-gray-500">of {formatTime(duration)}</p>
              </div>

              <div className="text-center">
                <p className="text-4xl font-bold text-blue-600">{focusScore}</p>
                <p className="text-sm text-gray-600">Focus score</p>
                <p className="text-xs mt-1 text-gray-500">
                  {focusScore >= 70 ? 'Locked in' : focusScore >= 50 ? 'Holding steady' : 'Drifting'}
                </p>
              </div>
            </div>

            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <video ref={videoRef} autoPlay muted className="w-full rounded border" />

              <div className="bg-gray-50 p-4 rounded border space-y-2 text-sm">
                <h3 className="font-semibold text-gray-800 mb-2">Session stats</h3>
                <div className="flex justify-between">
                  <span>Type</span>
                  <span className="font-medium capitalize">{sessionType}</span>
                </div>
                <div className="flex justify-between">
                  <span>Elapsed</span>
                  <span className="font-medium">{formatTime(sessionTime)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Remaining</span>
                  <span className="font-medium">{formatTime(Math.max(duration - sessionTime, 0))}</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg focus</span>
                  <span className="font-medium">{focusScore}</span>
                </div>
              </div>
            </div>

            {focusScore < 40 && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded text-sm space-y-2">
                <p className="font-semibold text-yellow-800">Tip: reset your attention</p>
                <ul className="list-disc list-inside text-yellow-900 space-y-1">
                  <li>Stand up and stretch for 30 seconds</li>
                  <li>Take three deep nasal breaths</li>
                  <li>Close distracting tabs or apps</li>
                </ul>
              </div>
            )}

            <button
              onClick={stopSession}
              className="w-full bg-red-600 text-white py-3 rounded-lg font-semibold hover:bg-red-700 transition"
            >
              End Session
            </button>
          </section>
        )}
      </div>
    </main>
  );
}
