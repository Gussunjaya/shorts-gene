import React from 'react';
import { AbsoluteFill, Audio, staticFile } from 'remotion';
import { Captions, WordToken } from './Captions';
import subtitlesData from '../subtitles.json';

export const ShortsComposition = () => {
  const words = subtitlesData as WordToken[];

  return (
    <AbsoluteFill style={{
      background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      color: 'white'
    }}>
      {/* Audio Utama (Durasi video otomatis mengikuti panjang audio ini) */}
      <Audio src={staticFile('final_audio.mp3')} />

      {/* Subtitle animasi per kata */}
      <Captions words={words} />
    </AbsoluteFill>
  );
};
