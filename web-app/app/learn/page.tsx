'use client';

import { useState } from 'react';

interface Flashcard {
  id: string;
  front: string;
  back: string;
  intervalDays: number;
}

const SAMPLE_CARDS: Flashcard[] = [
  {
    id: '1',
    front: 'Temporal Model Selection (TMS)',
    back: 'Choosing the identity/role that best fits the demands of the current context.',
    intervalDays: 1,
  },
  {
    id: '2',
    front: 'Myth of Objectivity Hypothesis (MOH)',
    back: 'Assumes there is no single neutral perspective; productivity is about coherence across selves.',
    intervalDays: 3,
  },
];

export default function LearningPage() {
  const [activeCardIndex, setActiveCardIndex] = useState(0);
  const activeCard = SAMPLE_CARDS[activeCardIndex];

  const handleNextCard = () => {
    setActiveCardIndex((prev) => (prev + 1) % SAMPLE_CARDS.length);
  };

  return (
    <main className="min-h-screen p-8 md:p-12 bg-gray-50">
      <div className="max-w-3xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl md:text-4xl font-bold">Learning</h1>
          <p className="text-gray-600 mt-2">
            Spaced repetition tuned to your active goals and current temporal model. We&apos;ll sync with
            Supabase shortly.
          </p>
        </header>

        <section className="bg-white p-8 rounded-lg shadow-sm space-y-6">
          <div className="border rounded-lg p-6 bg-gray-50">
            <p className="text-sm uppercase tracking-wide text-blue-600 font-semibold mb-2">
              Interval: {activeCard.intervalDays} day(s)
            </p>
            <h2 className="text-2xl font-semibold mb-4">{activeCard.front}</h2>
            <p className="text-gray-700">{activeCard.back}</p>
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleNextCard}
              className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Next Card
            </button>
            <button
              onClick={() => alert('TODO: Integrate Supabase reviews')}
              className="flex-1 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition"
            >
              Mark Reviewed
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
