declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: string;
    VUE_ROUTER_MODE: 'hash' | 'history' | 'abstract' | undefined;
    VUE_ROUTER_BASE: string | undefined;
  }
}

interface ImportMetaEnv {
  /** GitHub blob 루트 (예: https://github.com/owner/repo/blob/main) */
  readonly VITE_EXAM_JSON_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
