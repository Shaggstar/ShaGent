import { NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export const runtime = 'nodejs';

export async function POST(request: Request) {
  try {
    const { goals, timeAvailable, energyLevel } = await request.json();

    const prompt = `You are a task generation assistant. Generate 3-5 actionable tasks for today based on these goals:

Goals:
${JSON.stringify(goals, null, 2)}

Context:
- Time available: ${timeAvailable} hours
- Energy level: ${energyLevel}/5

Generate tasks that:
1. Are specific and actionable (SMART criteria)
2. Match the user's current energy level
3. Fit within available time
4. Progress toward the stated goals

Return ONLY valid JSON in this exact format:
{
  "tasks": [
    {
      "title": "Task description",
      "minutes": 60,
      "energy": "low" | "medium" | "high",
      "priority": 1,
      "goalId": "goal_id from input"
    }
  ]
}`;

    const response = await openai.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: prompt }],
      response_format: { type: 'json_object' },
      temperature: 0.7,
    });

    const content = response.choices[0]?.message?.content ?? '{"tasks": []}';
    const tasks = JSON.parse(content);

    return NextResponse.json(tasks);
  } catch (error) {
    console.error('Error generating tasks:', error);
    return NextResponse.json({ error: 'Failed to generate tasks' }, { status: 500 });
  }
}
