'use client';

import { useEffect, useState } from 'react';

interface TaskBlock {
  id: string;
  title: string;
  start: string;
  end: string;
  energy: 'low' | 'medium' | 'high';
}

const MOCK_BLOCKS: TaskBlock[] = [
  {
    id: '1',
    title: 'Morning focus block',
    start: '09:00',
    end: '10:30',
    energy: 'high',
  },
  {
    id: '2',
    title: 'Deep research',
    start: '11:00',
    end: '12:30',
    energy: 'high',
  },
  {
    id: '3',
    title: 'Async updates',
    start: '14:00',
    end: '15:00',
    energy: 'medium',
  },
];

export default function SchedulePage() {
  const [blocks, setBlocks] = useState<TaskBlock[]>([]);

  useEffect(() => {
    // TODO: Replace with Supabase fetch and calendar sync.
    setBlocks(MOCK_BLOCKS);
  }, []);

  return (
    <main className="min-h-screen p-8 md:p-12 bg-gray-50">
      <div className="max-w-4xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl md:text-4xl font-bold">Schedule</h1>
          <p className="text-gray-600 mt-2">
            See your calendar alongside temporal energy zones. We&apos;ll surface friction and offer
            adjustments soon.
          </p>
        </header>

        <section className="bg-white p-6 rounded-lg shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Today&apos;s blocks</h2>
          <ul className="space-y-3">
            {blocks.map((block) => (
              <li
                key={block.id}
                className="border rounded p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-semibold">{block.title}</p>
                  <p className="text-sm text-gray-500">
                    {block.start} – {block.end}
                  </p>
                </div>
                <span className="mt-2 sm:mt-0 inline-flex items-center text-sm uppercase tracking-wide">
                  Energy:&nbsp;
                  <span
                    className={
                      block.energy === 'high'
                        ? 'text-red-500'
                        : block.energy === 'medium'
                        ? 'text-yellow-600'
                        : 'text-green-600'
                    }
                  >
                    {block.energy}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
