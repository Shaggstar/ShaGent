export default function Home() {
  return (
    <main className="min-h-screen p-12 md:p-24">
      <div className="max-w-5xl mx-auto space-y-10">
        <header>
          <p className="text-sm uppercase tracking-wide text-blue-600 font-semibold">Better Self</p>
          <h1 className="text-4xl md:text-5xl font-bold mt-2">Your command center for deliberate days</h1>
          <p className="mt-4 text-lg text-gray-600">
            Start in Obsidian to set intent, then launch deeper tools in the web app for focus sessions,
            interview practice, and schedule optimization. Everything syncs through Supabase.
          </p>
        </header>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <a href="/focus" className="p-6 border rounded-lg hover:bg-gray-50 transition">
            <h2 className="text-2xl font-semibold mb-1 flex items-center gap-2">
              <span role="img" aria-label="Target">
                🎯
              </span>
              Focus Session
            </h2>
            <p className="text-gray-600">
              Start a deep work block with live attention tracking and actionable feedback.
            </p>
          </a>

          <a href="/interview" className="p-6 border rounded-lg hover:bg-gray-50 transition">
            <h2 className="text-2xl font-semibold mb-1 flex items-center gap-2">
              <span role="img" aria-label="Microphone">
                🎤
              </span>
              Interview Practice
            </h2>
            <p className="text-gray-600">
              Record behavioral answers, get transcription, and see STAR coverage instantly.
            </p>
          </a>

          <a href="/schedule" className="p-6 border rounded-lg hover:bg-gray-50 transition">
            <h2 className="text-2xl font-semibold mb-1 flex items-center gap-2">
              <span role="img" aria-label="Calendar">
                📅
              </span>
              Schedule
            </h2>
            <p className="text-gray-600">
              Visualize today&apos;s plan, energy curves, and high-leverage goals side by side.
            </p>
          </a>

          <a href="/learn" className="p-6 border rounded-lg hover:bg-gray-50 transition">
            <h2 className="text-2xl font-semibold mb-1 flex items-center gap-2">
              <span role="img" aria-label="Books">
                📚
              </span>
              Learning
            </h2>
            <p className="text-gray-600">
              Dive into spaced repetition cards pulled from your active goals and research threads.
            </p>
          </a>
        </section>
      </div>
    </main>
  );
}
