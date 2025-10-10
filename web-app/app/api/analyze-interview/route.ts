import { NextResponse } from 'next/server';
import OpenAI from 'openai';
import fs from 'fs';
import path from 'path';
import { writeFile } from 'fs/promises';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export const runtime = 'nodejs';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const audioFile = formData.get('audio') as File | null;

    if (!audioFile) {
      return NextResponse.json({ error: 'No audio file provided' }, { status: 400 });
    }

    const bytes = await audioFile.arrayBuffer();
    const buffer = Buffer.from(bytes);
    const tempPath = path.join('/tmp', `interview-${Date.now()}.webm`);
    await writeFile(tempPath, buffer);

    const transcription = await openai.audio.transcriptions.create({
      file: fs.createReadStream(tempPath),
      model: 'whisper-1',
    });

    const text = transcription.text ?? '';
    const analysis = analyzeTranscript(text);

    fs.unlinkSync(tempPath);

    return NextResponse.json({
      transcription: text,
      ...analysis,
    });
  } catch (error) {
    console.error('Error analyzing interview:', error);
    return NextResponse.json({ error: 'Failed to analyze interview' }, { status: 500 });
  }
}

function analyzeTranscript(text: string) {
  const words = text.split(/\s+/).filter((word) => word.length > 0);
  const sentences = text.split(/[.!?]+/).filter((sentence) => sentence.trim().length > 0);

  const fillerWords = ['um', 'uh', 'like', 'you know', 'kind of', 'sort of'];
  const lower = text.toLowerCase();
  let fillerCount = 0;
  fillerWords.forEach((token) => {
    const matches = lower.match(new RegExp(`\\b${token}\\b`, 'gi'));
    if (matches) {
      fillerCount += matches.length;
    }
  });

  const estimatedMinutes = Math.max(words.length / 150, 1 / 60);
  const fillerWordsPerMinute = fillerCount / estimatedMinutes;
  const wordsPerMinute = Math.round(words.length / estimatedMinutes);
  const clarity = sentences.length > 0 ? words.length / sentences.length : words.length;

  const hasSituation = /situation|context|background|at the time|working on/i.test(text);
  const hasTask = /task|goal|objective|responsible|needed to/i.test(text);
  const hasAction = /action|did|implemented|created|developed|decided|worked with/i.test(text);
  const hasResult = /result|outcome|impact|increased|decreased|improved|achieved/i.test(text);

  return {
    fillerWordsPerMinute,
    wordsPerMinute,
    clarity,
    starStructure: {
      hasSituation,
      hasTask,
      hasAction,
      hasResult,
    },
  };
}
