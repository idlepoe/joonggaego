declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: string;
    VUE_ROUTER_MODE: 'hash' | 'history' | 'abstract' | undefined;
    VUE_ROUTER_BASE: string | undefined;
  }
}

interface ImportMetaEnv {
  /** GitHub Raw 루트 (예: https://raw.githubusercontent.com/owner/repo/main) */
  readonly VITE_EXAM_RAW_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
