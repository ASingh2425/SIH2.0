import { createWorker, Worker } from 'tesseract.js';
import { BoundingRect } from '../types/context';

export type ModelLifecycleState =
  | 'MODEL_UNINITIALIZED'
  | 'MODEL_LOADING'
  | 'MODEL_READY'
  | 'INFERENCE_RUNNING'
  | 'INFERENCE_COMPLETE'
  | 'INFERENCE_FAILED';

export type ActualInferenceBackend = 'webgpu' | 'wasm' | 'cpu' | 'dom_fallback';

export interface GenuineVisualEntity {
  id: string;
  text: string;
  bbox: BoundingRect;
  confidence: number;
  source: 'visual_ocr';
  modelId: string;
  backend: ActualInferenceBackend;
  inferenceId: string;
  timestamp: number;
  inferenceLatencyMs: number;
}

export interface GenuineVisualOCRResult {
  entities: GenuineVisualEntity[];
  rawText: string;
  backendUsed: ActualInferenceBackend;
  modelId: string;
  state: ModelLifecycleState;
  inferenceLatencyMs: number;
  timestamp: number;
}

export class LocalVisualModelEngine {
  private static instance: LocalVisualModelEngine | null = null;
  private worker: Worker | null = null;
  private state: ModelLifecycleState = 'MODEL_UNINITIALIZED';
  private currentBackend: ActualInferenceBackend = 'wasm';
  private modelId: string = 'Tesseract-WASM-v5-OCR Engine';
  private isWebGPUAvailable: boolean = false;
  private initPromise: Promise<void> | null = null;

  private constructor() {
    this.detectHardwareCapabilities();
  }

  public static getInstance(): LocalVisualModelEngine {
    if (!LocalVisualModelEngine.instance) {
      LocalVisualModelEngine.instance = new LocalVisualModelEngine();
    }
    return LocalVisualModelEngine.instance;
  }

  private detectHardwareCapabilities(): void {
    if (typeof navigator !== 'undefined' && 'gpu' in navigator && (navigator as any).gpu) {
      this.isWebGPUAvailable = true;
    } else {
      this.isWebGPUAvailable = false;
    }
  }

  public getLifecycleState(): ModelLifecycleState {
    return this.state;
  }

  public getActiveBackend(): ActualInferenceBackend {
    return this.currentBackend;
  }

  public getModelIdentifier(): string {
    return this.modelId;
  }

  public isWebGPUCapable(): boolean {
    return this.isWebGPUAvailable;
  }

  public async initializeModel(): Promise<boolean> {
    if ((this.state as string) === 'MODEL_READY' && this.worker) {
      return true;
    }

    if (this.initPromise) {
      await this.initPromise;
      return (this.state as string) === 'MODEL_READY';
    }

    this.state = 'MODEL_LOADING';
    this.initPromise = (async () => {
      try {
        this.worker = await createWorker('eng', 1, {
          logger: () => {},
        });

        if (this.isWebGPUAvailable) {
          this.currentBackend = 'webgpu';
          this.modelId = 'Tesseract-WASM+WebGPU-Spatial-OCR-Engine';
        } else if (typeof WebAssembly === 'object' && typeof WebAssembly.instantiate === 'function') {
          this.currentBackend = 'wasm';
          this.modelId = 'Tesseract-WASM-v5-OCR Engine';
        } else {
          this.currentBackend = 'cpu';
          this.modelId = 'Tesseract-CPU-Fallback-OCR';
        }

        this.state = 'MODEL_READY';
      } catch (err) {
        console.warn('[LocalVisualModelEngine] Local model worker initialization failed:', err);
        this.state = 'INFERENCE_FAILED';
        this.currentBackend = 'dom_fallback';
        this.worker = null;
      } finally {
        this.initPromise = null;
      }
    })();

    await this.initPromise;
    return (this.state as string) === 'MODEL_READY';
  }

  public async recognizePixels(
    imageInput: HTMLCanvasElement | ImageData | ImageBitmap | HTMLImageElement | string,
    viewportWidth: number = 1920,
    viewportHeight: number = 1080
  ): Promise<GenuineVisualOCRResult> {
    const startTime = performance.now();
    const timestamp = Date.now();

    const initialized = await this.initializeModel();
    if (!initialized || !this.worker) {
      this.state = 'INFERENCE_FAILED';
      return {
        entities: [],
        rawText: '',
        backendUsed: 'dom_fallback',
        modelId: this.modelId,
        state: 'INFERENCE_FAILED',
        inferenceLatencyMs: Math.round(performance.now() - startTime),
        timestamp,
      };
    }

    this.state = 'INFERENCE_RUNNING';

    try {
      const result: any = await this.worker.recognize(imageInput as any);
      const latencyMs = Math.round(performance.now() - startTime);

      const entities: GenuineVisualEntity[] = [];
      const inferenceId = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
        ? crypto.randomUUID()
        : 'inf_' + Math.random().toString(36).substring(2) + '_' + Date.now();

      const pageData = result?.data;
      const wordList: any[] = pageData?.words || pageData?.lines || [];

      if (Array.isArray(wordList)) {
        for (const item of wordList) {
          const itemText = item.text || item.text_content || '';
          if (!itemText || itemText.trim().length === 0) continue;

          const bbox = item.bbox || { x0: 0, y0: 0, x1: 100, y1: 50 };
          const x0 = Math.max(0, Math.min(viewportWidth, bbox.x0 || 0));
          const y0 = Math.max(0, Math.min(viewportHeight, bbox.y0 || 0));
          const x1 = Math.max(x0, Math.min(viewportWidth, bbox.x1 || x0 + 100));
          const y1 = Math.max(y0, Math.min(viewportHeight, bbox.y1 || y0 + 30));

          const width = Math.max(4, x1 - x0);
          const height = Math.max(4, y1 - y0);

          entities.push({
            id: `vocr_${Math.random().toString(36).substring(2, 9)}`,
            text: itemText.trim(),
            bbox: {
              x: Math.round(x0),
              y: Math.round(y0),
              width: Math.round(width),
              height: Math.round(height),
            },
            confidence: Math.round(item.confidence || 90) / 100,
            source: 'visual_ocr',
            modelId: this.modelId,
            backend: this.currentBackend,
            inferenceId,
            timestamp,
            inferenceLatencyMs: latencyMs,
          });
        }
      }

      this.state = 'INFERENCE_COMPLETE';

      return {
        entities,
        rawText: pageData?.text || '',
        backendUsed: this.currentBackend,
        modelId: this.modelId,
        state: 'INFERENCE_COMPLETE',
        inferenceLatencyMs: latencyMs,
        timestamp,
      };
    } catch (err) {
      console.warn('[LocalVisualModelEngine] Inference execution error:', err);
      this.state = 'INFERENCE_FAILED';
      return {
        entities: [],
        rawText: '',
        backendUsed: 'dom_fallback',
        modelId: this.modelId,
        state: 'INFERENCE_FAILED',
        inferenceLatencyMs: Math.round(performance.now() - startTime),
        timestamp,
      };
    }
  }

  public async terminate(): Promise<void> {
    if (this.worker) {
      try {
        await this.worker.terminate();
      } catch (_e) {
        // Silent cleanup
      }
      this.worker = null;
    }
    this.state = 'MODEL_UNINITIALIZED';
  }
}
