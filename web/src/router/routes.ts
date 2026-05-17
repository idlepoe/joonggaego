import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/ExamLayout.vue'),
    children: [
      {
        path: '',
        name: 'exam-main',
        component: () => import('pages/exam/MainSubjectPage.vue'),
      },
      {
        path: 'options',
        name: 'exam-options',
        component: () => import('pages/exam/ExamOptionsPage.vue'),
      },
      {
        path: 'sessions/:subject',
        name: 'exam-sessions',
        component: () => import('pages/exam/SessionListPage.vue'),
        props: true,
      },
      {
        path: 'sheet/:subject/:session',
        name: 'exam-sheet',
        component: () => import('pages/exam/AnswerSheetPage.vue'),
        props: true,
      },
      {
        path: 'mock/:subject',
        name: 'exam-mock',
        component: () => import('pages/exam/MockExamPage.vue'),
        props: true,
      },
      {
        path: 'mock-review/:subject/:endedAt',
        name: 'exam-mock-review',
        component: () => import('pages/exam/MockExamReviewPage.vue'),
        props: true,
      },
    ],
  },

  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
