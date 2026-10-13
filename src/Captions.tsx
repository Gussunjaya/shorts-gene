import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';

export interface WordToken {
  word: string;
  start: number;
  end: number;
}

export const Captions: React.FC<{ words: WordToken[] }> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const currentWord = words.find(w => currentTime >= w.start && currentTime <= w.end);

  if (!currentWord) return null;

  return (
    <div style={{
      position: 'absolute',
      bottom: '30%',
      width: '100%',
      textAlign: 'center',
      padding: '0 40px',
    }}>
      <span style={{
        fontSize: '70px',
        fontWeight: '900',
        color: '#FFD700',
        textTransform: 'uppercase',
        textShadow: '4px 4px 10px rgba(0,0,0,0.9)',
        backgroundColor: 'rgba(0,0,0,0.6)',
        padding: '10px 25px',
        borderRadius: '15px',
        fontFamily: 'sans-serif'
      }}>
        {currentWord.word}
      </span>
    </div>
  );
};
