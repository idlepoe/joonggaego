<template>
  <aside class="exam-app-intro-rail" aria-label="앱 소개">
    <q-scroll-area class="fit">
      <div class="exam-app-intro-rail__inner q-pa-md">
        <img
          class="exam-app-intro-rail__icon rounded-borders"
          src="/icons/icon.png"
          width="72"
          height="72"
          alt=""
        />
        <div class="text-h6 text-weight-bold q-mt-sm">광고없는주택관리사1차기출회독</div>
        <p class="text-body2 text-grey-8 q-mt-sm q-mb-md">
          주택관리사보수능력검정 <strong>1차</strong> 기출을 회독·모의고사 형태로 학습할 수 있는
          <strong>광고 없음</strong> 웹·앱입니다.
        </p>

        <div class="text-subtitle2 text-weight-medium q-mb-xs">앱 소개</div>
        <ul class="exam-app-intro-rail__list text-body2 text-grey-9">
          <li>회차별 기출 <strong>회독</strong>: 정답을 바로 확인하며 반복 학습합니다.</li>
          <li><strong>모의고사</strong>: 풀이·채점·이력 확인이 가능합니다.</li>
          <li>일부 진행 상태가 기기에 저장됩니다.</li>
          <li>광고가 없습니다.</li>
        </ul>

        <div class="text-subtitle2 text-weight-medium q-mt-md q-mb-xs">이런 분께</div>
        <ul class="exam-app-intro-rail__list text-body2 text-grey-9">
          <li>기출을 <strong>빠르게 여러 번</strong> 훑고 싶은 분</li>
          <li>문제·정답을 <strong>세트로</strong> 외우는 분</li>
          <li><strong>집중</strong>해서 보고 싶은 분</li>
        </ul>

        <div class="text-subtitle2 text-weight-medium q-mt-md q-mb-xs">학습 흐름</div>
        <ol class="exam-app-intro-rail__ol text-body2 text-grey-9">
          <li>과목 선택</li>
          <li><strong>회독</strong> 또는 <strong>모의고사</strong> 진행</li>
          <li>설정에서 글자 크기·하단 버튼 등 조절</li>
        </ol>

        <div class="text-subtitle2 text-weight-medium q-mt-md q-mb-xs">소스 코드</div>
        <p class="text-body2 q-mb-md">
          <a
            class="text-primary"
            href="https://github.com/idlepoe/jootaek_exam"
            target="_blank"
            rel="noopener noreferrer"
          >
            github.com/idlepoe/jootaek_exam
          </a>
        </p>

        <div class="text-subtitle2 text-weight-medium q-mb-xs">문의</div>
        <p class="text-body2 text-grey-9 q-mb-none">
          문제·문의는
          <a class="text-primary" href="mailto:idlepoe@gmail.com">idlepoe@gmail.com</a>
          으로 보내 주세요.
        </p>
      </div>
    </q-scroll-area>
  </aside>
</template>

<script setup lang="ts">
// 정적 소개 레일(프롭 없음)
</script>

<style scoped>
.exam-app-intro-rail {
  background-color: transparent;
  color: rgba(0, 0, 0, 0.87);
}
.body--dark .exam-app-intro-rail {
  background-color: transparent;
  color: rgba(255, 255, 255, 0.88);
}

/* 라이트: Quasar grey 유틸 유지. 다크: 라이트용 grey가 배경과 겹침 → 명시적 대비 */
.body--dark .exam-app-intro-rail .text-grey-8,
.body--dark .exam-app-intro-rail .text-grey-9 {
  color: rgba(255, 255, 255, 0.72) !important;
}

.body--dark .exam-app-intro-rail .text-h6 {
  color: #fff !important;
}

.body--dark .exam-app-intro-rail .text-subtitle2 {
  color: rgba(255, 255, 255, 0.92) !important;
}

.body--dark .exam-app-intro-rail strong {
  color: #fff;
}

.body--dark .exam-app-intro-rail .text-primary {
  color: var(--q-primary) !important;
}

.exam-app-intro-rail__inner {
  max-width: 100%;
}
.exam-app-intro-rail__icon {
  display: block;
}
.exam-app-intro-rail__list,
.exam-app-intro-rail__ol {
  margin: 0;
  padding-left: 1.25rem;
}
.exam-app-intro-rail__list li + li,
.exam-app-intro-rail__ol li + li {
  margin-top: 0.35rem;
}
</style>
