let stream = null;
let sampling = false;
let sampleBuffer = [];
let sampleStartTime = 0;
const SAMPLE_DURATION_MS = 15000; // 15s scan window
const SAMPLE_INTERVAL_MS = 100;   // ~10 samples/sec

const video = document.getElementById('camVideo');
const camFrame = document.getElementById('camFrame');
const camPlaceholder = document.getElementById('camPlaceholder');
const camStatus = document.getElementById('camStatus');
const camStatusText = document.getElementById('camStatusText');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const resultCard = document.getElementById('resultCard');
const bpmValue = document.getElementById('bpmValue');
const signalBadge = document.getElementById('signalBadge');
const resultNote = document.getElementById('resultNote');
const lowSignalBox = document.getElementById('lowSignalBox');

// hidden canvas used to read pixel data from video frames
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d', { willReadFrequently: true });

async function startCheck() {
  resultCard.classList.remove('show');
  lowSignalBox.classList.remove('show');

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 480 }, height: { ideal: 360 } },
      audio: false
    });
  } catch (err) {
    setStatus('Camera access denied or unavailable', false);
    return;
  }

  video.srcObject = stream;
  camFrame.classList.add('active');
  startBtn.style.display = 'none';
  stopBtn.style.display = 'inline-block';
  setStatus('Position your face in the circle', true);

  video.onloadedmetadata = () => {
    canvas.width = video.videoWidth || 480;
    canvas.height = video.videoHeight || 360;
    // brief pause so user can position face before sampling starts
    setTimeout(beginSampling, 1500);
  };
}

function beginSampling() {
  sampling = true;
  sampleBuffer = [];
  sampleStartTime = performance.now();
  camFrame.classList.add('scanning');
  setStatus('Scanning… hold still', true, true);
  requestAnimationFrame(sampleLoop);
}

function sampleLoop(now) {
  if (!sampling) return;

  const elapsed = performance.now() - sampleStartTime;

  try {
    // draw current frame to hidden canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // sample a center region (rough stand-in for a face ROI —
    // real implementation should use MediaPipe landmarks for forehead/cheek)
    const roiW = Math.floor(canvas.width * 0.3);
    const roiH = Math.floor(canvas.height * 0.3);
    const roiX = Math.floor((canvas.width - roiW) / 2);
    const roiY = Math.floor((canvas.height - roiH) / 2);
    const frame = ctx.getImageData(roiX, roiY, roiW, roiH).data;

    // average green channel (green is most sensitive to blood-volume changes)
    let sum = 0;
    let count = 0;
    for (let i = 0; i < frame.length; i += 4) {
      sum += frame[i + 1]; // green channel
      count++;
    }
    const avgGreen = sum / count;
    sampleBuffer.push({ t: elapsed, v: avgGreen });
  } catch (e) {
    // frame not ready yet, skip
  }

  if (elapsed < SAMPLE_DURATION_MS) {
    setTimeout(() => requestAnimationFrame(sampleLoop), SAMPLE_INTERVAL_MS);
  } else {
    finishSampling();
  }
}

function finishSampling() {
  sampling = false;
  camFrame.classList.remove('scanning');
  setStatus('Analyzing…', true);

  const result = estimateBpmFromSamples(sampleBuffer);
  showResult(result);
  stopCamera();
}

// ------------------------------------------------------------
// Naive peak-counting BPM estimate + signal-quality heuristic.
// This is intentionally simple — replace with backend FFT pipeline
// for anything beyond prototype/demo purposes.
// ------------------------------------------------------------
function estimateBpmFromSamples(samples) {
  if (samples.length < 30) {
    return { bpm: null, quality: 'low' };
  }

  const values = samples.map(s => s.v);
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length;
  const stdDev = Math.sqrt(variance);

  // very low variance usually means poor lighting / no real signal
  if (stdDev < 0.15) {
    return { bpm: null, quality: 'low' };
  }

  // simple peak counting above the mean line
  let peaks = 0;
  for (let i = 1; i < values.length - 1; i++) {
    if (values[i] > mean && values[i] > values[i - 1] && values[i] > values[i + 1]) {
      peaks++;
    }
  }

  const durationSec = (samples[samples.length - 1].t - samples[0].t) / 1000;
  const bpm = Math.round((peaks / durationSec) * 60);

  // sanity-clamp: outside plausible human resting range → treat as unreliable
  if (bpm < 40 || bpm > 180) {
    return { bpm: null, quality: 'low' };
  }

  const quality = stdDev > 0.4 ? 'good' : 'fair';
  return { bpm, quality };
}

async function showResult({ bpm, quality }) {
  resultCard.classList.add('show');

  if (bpm === null || quality === 'low') {
    bpmValue.textContent = '--';
    signalBadge.textContent = 'Signal too low';
    signalBadge.className = 'signal-badge signal-low';
    resultNote.style.display = 'none';
    lowSignalBox.classList.add('show');
    setStatus('Signal quality too low', false);
  } else {
    lowSignalBox.classList.remove('show');
    resultNote.style.display = 'block';
    bpmValue.textContent = bpm;

    if (quality === 'good') {
      signalBadge.textContent = 'Good signal';
      signalBadge.className = 'signal-badge signal-good';
    } else {
      signalBadge.textContent = 'Fair signal';
      signalBadge.className = 'signal-badge signal-fair';
    }
    setStatus('Check complete', false);
  }

  // Log the derived {bpm, quality} to the backend so the digital twin can
  // recompute — raw video/frames are never sent, only this numeric result.
  try {
    if (typeof isLoggedIn === 'function' && isLoggedIn() && typeof submitPhysiology === 'function') {
      await submitPhysiology({ bpm, quality });
    }
  } catch (err) {
    console.warn('Could not save physiology reading:', err.message);
  }
}

function stopCheck() {
  sampling = false;
  stopCamera();
  setStatus('Camera stopped', false);
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
  camFrame.classList.remove('active', 'scanning');
  startBtn.style.display = 'inline-block';
  stopBtn.style.display = 'none';
}

function setStatus(text, ready, scanning = false) {
  camStatusText.textContent = text;
  camStatus.classList.toggle('ready', ready && !scanning);
  camStatus.classList.toggle('scanning', scanning);
}
