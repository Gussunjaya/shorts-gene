import React from 'react';
import { Composition } from 'remotion';
import { ShortsComposition } from './ShortsComposition';
import subtitlesData from '../subtitles.json';

export const Root = () => {
  // Hitung durasi total dalam detik dari kata terakhir di subtitle
  const lastWord = subtitlesData[subtitlesData.length - 1];
  const durationInSeconds = lastWord ? lastWord.end + 1 : 30;
  const fps = 30;
  const durationInFrames = Math.ceil(durationInSeconds * fps);

  return (
    <Composition
      id="ShortsComposition"
      component={ShortsComposition}
      durationInFrames={durationInFrames}
      fps={fps}
      width={1080}
      height={1920}
    />
  );
};
