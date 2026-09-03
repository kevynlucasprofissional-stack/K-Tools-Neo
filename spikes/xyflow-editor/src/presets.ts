import { type Node, type Edge } from '@xyflow/react';

export interface WorkflowPreset {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  nodes: Node[];
  edges: Edge[];
}

export const WORKFLOW_PRESETS: WorkflowPreset[] = [
  {
    id: 'audio-extract-convert',
    name: 'Extrair e Converter Áudio (Lote)',
    description: 'Varre uma pasta de vídeos, extrai o áudio em WAV e converte para M4A ALAC lossless.',
    category: 'Mídia',
    icon: '🎬',
    nodes: [
      {
        id: 'p1-1',
        type: 'ktool',
        position: { x: 50, y: 120 },
        data: {
          type_id: 'folder.literal',
          label: 'Pasta de Entrada',
          category: 'Files',
          inputs: [],
          outputs: [{ id: 'folder', type: 'folder', label: 'folder' }],
          config: { path: 'C:/Projetos/Videos' },
          runState: 'IDLE',
        },
      },
      {
        id: 'p1-2',
        type: 'ktool',
        position: { x: 360, y: 120 },
        data: {
          type_id: 'folder.scan_files',
          label: 'Scan Folder Files',
          category: 'Files',
          inputs: [{ id: 'folder', type: 'folder', label: 'folder' }],
          outputs: [
            { id: 'files', type: 'files', label: 'files' },
            { id: 'report', type: 'json', label: 'report' },
          ],
          config: { recursive: true, extensions: 'mp4,mkv' },
          runState: 'IDLE',
        },
      },
      {
        id: 'p1-3',
        type: 'ktool',
        position: { x: 680, y: 120 },
        data: {
          type_id: 'media.extract_audio',
          label: 'Extract Audio',
          category: 'Media',
          inputs: [{ id: 'file', type: 'file', label: 'file' }],
          outputs: [{ id: 'audio', type: 'file', label: 'audio' }],
          config: { format: 'wav' },
          runState: 'IDLE',
        },
      },
      {
        id: 'p1-4',
        type: 'ktool',
        position: { x: 1000, y: 120 },
        data: {
          type_id: 'media.convert_lossless_alac',
          label: 'Convert to Lossless ALAC',
          category: 'Media',
          inputs: [{ id: 'file', type: 'file', label: 'file' }],
          outputs: [{ id: 'output_file', type: 'file', label: 'output_file' }],
          config: { keep_source: true },
          runState: 'IDLE',
        },
      },
    ],
    edges: [
      { id: 'pe1-2', source: 'p1-1', target: 'p1-2', sourceHandle: 'folder', targetHandle: 'folder', animated: true, style: { stroke: '#eab308', strokeWidth: 2 } },
      { id: 'pe2-3', source: 'p1-2', target: 'p1-3', sourceHandle: 'files', targetHandle: 'file', animated: true, style: { stroke: '#38bdf8', strokeWidth: 2 } },
      { id: 'pe3-4', source: 'p1-3', target: 'p1-4', sourceHandle: 'audio', targetHandle: 'file', animated: true, style: { stroke: '#38bdf8', strokeWidth: 2 } },
    ],
  },
  {
    id: 'audio-studio-deess',
    name: 'Master de Áudio & De-Esser',
    description: 'Une múltiplos áudios com ordenação natural, normaliza volume e aplica de-esser de voz.',
    category: 'Áudio',
    icon: '🎙️',
    nodes: [
      {
        id: 'p2-1',
        type: 'ktool',
        position: { x: 80, y: 150 },
        data: {
          type_id: 'files.literal',
          label: 'Arquivos de Voz',
          category: 'Files',
          inputs: [],
          outputs: [{ id: 'files', type: 'files', label: 'files' }],
          config: { paths: 'take1.wav, take2.wav, take3.wav' },
          runState: 'IDLE',
        },
      },
      {
        id: 'p2-2',
        type: 'ktool',
        position: { x: 420, y: 150 },
        data: {
          type_id: 'media.merge_audio_studio',
          label: 'Merge Audio Studio',
          category: 'Media',
          inputs: [{ id: 'files', type: 'files', label: 'files' }],
          outputs: [{ id: 'output_file', type: 'file', label: 'output_file' }],
          config: { normalize: true, sample_rate: 44100 },
          runState: 'IDLE',
        },
      },
      {
        id: 'p2-3',
        type: 'ktool',
        position: { x: 780, y: 150 },
        data: {
          type_id: 'media.deess_audio',
          label: 'De-ess Audio',
          category: 'Media',
          inputs: [{ id: 'file', type: 'file', label: 'file' }],
          outputs: [{ id: 'output_file', type: 'file', label: 'output_file' }],
          config: { intensity: 0.5, denoise: true },
          runState: 'IDLE',
        },
      },
    ],
    edges: [
      { id: 'pe2-1-2', source: 'p2-1', target: 'p2-2', sourceHandle: 'files', targetHandle: 'files', animated: true, style: { stroke: '#38bdf8', strokeWidth: 2 } },
      { id: 'pe2-2-3', source: 'p2-2', target: 'p2-3', sourceHandle: 'output_file', targetHandle: 'file', animated: true, style: { stroke: '#c084fc', strokeWidth: 2 } },
    ],
  },
  {
    id: 'filesystem-audit',
    name: 'Auditoria de Pastas e Relatório',
    description: 'Audita a estrutura de diretórios gerando CSV tabular, árvore ASCII e métricas JSON.',
    category: 'Sistema',
    icon: '🗄️',
    nodes: [
      {
        id: 'p3-1',
        type: 'ktool',
        position: { x: 120, y: 160 },
        data: {
          type_id: 'folder.literal',
          label: 'Pasta Raiz',
          category: 'Files',
          inputs: [],
          outputs: [{ id: 'folder', type: 'folder', label: 'folder' }],
          config: { path: 'C:/Github/K-Tools-Neo' },
          runState: 'IDLE',
        },
      },
      {
        id: 'p3-2',
        type: 'ktool',
        position: { x: 500, y: 140 },
        data: {
          type_id: 'filesystem.structure_report',
          label: 'Export Structure Report',
          category: 'Filesystem',
          inputs: [{ id: 'root_dir', type: 'folder', label: 'root_dir' }],
          outputs: [
            { id: 'csv', type: 'file', label: 'csv' },
            { id: 'tree', type: 'file', label: 'tree' },
            { id: 'metrics', type: 'json', label: 'metrics' },
          ],
          config: { max_depth: 6 },
          runState: 'IDLE',
        },
      },
    ],
    edges: [
      { id: 'pe3-1-2', source: 'p3-1', target: 'p3-2', sourceHandle: 'folder', targetHandle: 'root_dir', animated: true, style: { stroke: '#eab308', strokeWidth: 2 } },
    ],
  },
  {
    id: 'cloud-stream-scanner',
    name: 'Scanner de Nuvem (Google Drive/OneDrive)',
    description: 'Varredura segura sem hidratação local de arquivos, salvando checkpoints em SQLite.',
    category: 'Sistema',
    icon: '☁️',
    nodes: [
      {
        id: 'p4-1',
        type: 'ktool',
        position: { x: 120, y: 160 },
        data: {
          type_id: 'folder.literal',
          label: 'Google Drive Virtual',
          category: 'Files',
          inputs: [],
          outputs: [{ id: 'folder', type: 'folder', label: 'folder' }],
          config: { path: 'G:/Meu Drive' },
          runState: 'IDLE',
        },
      },
      {
        id: 'p4-2',
        type: 'ktool',
        position: { x: 520, y: 140 },
        data: {
          type_id: 'filesystem.drive_stream_scan',
          label: 'Drive Streaming Scanner',
          category: 'Filesystem',
          inputs: [{ id: 'root_dir', type: 'folder', label: 'root_dir' }],
          outputs: [
            { id: 'database', type: 'file', label: 'database' },
            { id: 'csv', type: 'file', label: 'csv' },
            { id: 'report', type: 'json', label: 'report' },
          ],
          config: { safe_non_hydrating: true },
          runState: 'IDLE',
        },
      },
    ],
    edges: [
      { id: 'pe4-1-2', source: 'p4-1', target: 'p4-2', sourceHandle: 'folder', targetHandle: 'root_dir', animated: true, style: { stroke: '#eab308', strokeWidth: 2 } },
    ],
  },
  {
    id: 'tldv-transcript-extractor',
    name: 'Extrator de Reuniões tl;dv',
    description: 'Extrai transcrições de reuniões gravadas para Markdown com speakers, legendas SRT e JSON.',
    category: 'Texto',
    icon: '📝',
    nodes: [
      {
        id: 'p5-1',
        type: 'ktool',
        position: { x: 120, y: 160 },
        data: {
          type_id: 'file.literal',
          label: 'Página tl;dv (.html)',
          category: 'Files',
          inputs: [],
          outputs: [{ id: 'file', type: 'file', label: 'file' }],
          config: { path: 'reuniao_projeto.html' },
          runState: 'IDLE',
        },
      },
      {
        id: 'p5-2',
        type: 'ktool',
        position: { x: 500, y: 140 },
        data: {
          type_id: 'text.tldv_extract',
          label: 'Extrair Transcrição tl;dv',
          category: 'Text',
          inputs: [{ id: 'file', type: 'file', label: 'file' }],
          outputs: [
            { id: 'markdown', type: 'file', label: 'markdown' },
            { id: 'srt', type: 'file', label: 'srt' },
            { id: 'json', type: 'json', label: 'json' },
          ],
          config: {},
          runState: 'IDLE',
        },
      },
    ],
    edges: [
      { id: 'pe5-1-2', source: 'p5-1', target: 'p5-2', sourceHandle: 'file', targetHandle: 'file', animated: true, style: { stroke: '#38bdf8', strokeWidth: 2 } },
    ],
  },
];
