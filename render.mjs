// Renderiza un AlphaTex a wav con alphaTab. Se copia en kitara/scripts para correrlo:
// necesita el node_modules de ese repo.
import { readFileSync, writeFileSync } from 'node:fs';
import * as alphaTab from '@coderline/alphatab';
const [tex, out] = process.argv.slice(2);
const settings = new alphaTab.Settings();
const importer = new alphaTab.importer.AlphaTexImporter();
importer.initFromString(readFileSync(tex, 'utf8'), settings);
const score = importer.readScore();
const midi = new alphaTab.midi.MidiFile();
new alphaTab.midi.MidiFileGenerator(score, settings, new alphaTab.midi.AlphaSynthMidiFileHandler(midi, true)).generate();
const ev = () => ({ on() {}, off() {}, trigger() {} });
const output = { sampleRate: 44100, ready: ev(), samplesPlayed: ev(), sampleRequest: ev(), open() {}, play() {}, pause() {}, activate() {},
  addSamples() {}, resetSamples() {}, destroy() {}, enumerateOutputDevices: async () => [], setOutputDevice: async () => {}, getOutputDevice: async () => null };
const synth = new alphaTab.synth.AlphaSynth(output, 500);
const options = new alphaTab.synth.AudioExportOptions();
options.soundFonts = [new Uint8Array(readFileSync('public/soundfont/sonivox.sf2'))];
const exporter = synth.exportAudio(options, midi, [], new Map());
const chunks = []; let total = 0;
for (;;) { const c = exporter.render(1000); if (!c) break; chunks.push(c.samples); total += c.samples.length; if (total > 44100 * 2 * 600) break; }
const pcm = Buffer.alloc(44 + total * 2);
let peak = 0; for (const c of chunks) for (const v of c) peak = Math.max(peak, Math.abs(v));
const gain = peak > 0 ? Math.min(0.9 / peak, 4) : 1;
pcm.write('RIFF', 0); pcm.writeUInt32LE(36 + total * 2, 4); pcm.write('WAVEfmt ', 8); pcm.writeUInt32LE(16, 16); pcm.writeUInt16LE(1, 20);
pcm.writeUInt16LE(2, 22); pcm.writeUInt32LE(44100, 24); pcm.writeUInt32LE(44100 * 4, 28); pcm.writeUInt16LE(4, 32); pcm.writeUInt16LE(16, 34);
pcm.write('data', 36); pcm.writeUInt32LE(total * 2, 40);
let o = 44; for (const c of chunks) for (const v of c) { pcm.writeInt16LE(Math.round(Math.max(-1, Math.min(1, v * gain)) * 32767), o); o += 2; }
writeFileSync(out, pcm);
console.log('compases', score.masterBars.length, (total / 2 / 44100).toFixed(1) + ' s', 'pico', peak.toFixed(3));
