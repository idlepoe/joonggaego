[main]

회독 섹션 밑으로 모의고사 섹션 추가 표시
민법
회계원리
공동주택시설개론

각 subject를 버튼으로 표시

subject 정보를 가지고 mockExam 로 진입

[mockExam]

해당 subject에 해당하는 모든 jsons 문제 취득 후 subject를 기준으로 40개의 문항을 섞어서 표시
생성된 문항은 current_mock_exam 이름으로 localstorage에 저장

subject 과목
questions 랜덤문항 리스트
answers 체크한 답안 리스트
startedAt 시작한 시간
currentIndex 진행한 위치

*appbar
뒤로가기

toolbar엔 startedAt 시간으로부터 1분*생성한 문제수로 하여 실시간으로 진행시간이 표시될 것.
startedAt시간으로부터 지난시간(분,초) / {1분*생성한 문제}분

답안제출
 if answer가 작성되지 않은 문제가 존재할 경우
  풀지 않은 문제가 있습니다. 해당 문제로 이동하시겠습니까?
  예 누를 경우 anwser가 작성되지 않은 문제로 화면 이동
  채점 누를 경우 correct_answer와 answer를 비교하여 정답 개수를 확인하여 채점 결과 다이얼로그로 표시
   채점 결과 전체 문제의 60% 이상 정답일 경우 '합격' 표시
   정답 수 표시
   확인 버튼 누를 경우 current_mock_exam는 삭제하고 mock_exam_history 리스트트에 endedAt과 correctCount, isPassed 를 저장 후 back 화면 이동
  취소 누를 경우 취소
 else if answer가 전부 작성된 경우
  시험을 종료하시겠습니까?
   확인 current_mock_exam 는 삭제하고 back 화면 이동
   취소 취소

*body은 answerSheetPage와 동일하고
정답은 표시되지 않음.

보기를 선택할 경우 하이라이트 표시하고 0.5초 후 다음 문제로 진행됨.

*하단
이전 다음
다음 버튼을 누를때마다 currentIndex 를 1씩 증가
이전 버튼을 누를때마다 currentIndex 를 1씩 감소

더 이상 다음이 없을 경우 

 if answer가 작성되지 않은 문제가 존재할 경우
  풀지 않은 문제가 있습니다. 해당 문제로 이동하시겠습니까?
  예 누를 경우 anwser가 작성되지 않은 문제로 화면 이동
  채점 누를 경우 correct_answer와 answer를 비교하여 정답 개수를 확인하여 채점 결과 다이얼로그로 표시
   채점 결과 전체 문제의 60% 이상 정답일 경우 '합격' 표시
   정답 수 표시
   확인 버튼 누를 경우 current_mock_exam는 삭제하고 mock_exam_history 리스트트에 endedAt과 correctCount, isPassed 를 저장 후 back 화면 이동
  취소 누를 경우 취소
 else if answer가 전부 작성된 경우
  시험을 종료하시겠습니까?
   확인 current_mock_exam 는 삭제하고 back 화면 이동
   취소 취소

이전이 없을 경우 이전 비활성화