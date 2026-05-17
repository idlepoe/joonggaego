[main]

*appbar
광고없는주택관리사보1차

*body

-회독
민법
회계원리
공동주택시설개론

각 버튼으로 표시

선택시 해당 subject 정보를 가지고 session_list

[sessionList]

*appbar
뒤로가기 광고없는주택관리사보1차 회독
 
2025-06-28
2024-06-29
2023-07-08
2022-07-09
~
2008-09-07

각 버튼으로 표시

assets/jsons 의 파일 exam_session의 파일 정보를 json list 로 저장하고 있다가 해당 내용을 버튼 리스트로 표시

버튼 클릭시 subject 정보와 exam_session 정보를 바탕으로 해당 json 파일을 취득 

[answerSheet]

*appbar
뒤로가기

*body
{exam_type} {subject} {current_question_index}(현재문항)/{total_question_count}(총문항)
해당 내용은 최상단에 1줄로 현재 문제 현황 표시
question_text 를 표시하고 하단에 4개 choices를 block 형태로 표시하고 correct_answer에 해당하는 choices 는 하이라이트 표시

*bottom
이전 다음

다음 버튼을 누를때마다 current_question_index 를 1씩 증가
이전 버튼을 누를때마다 current_question_index 1씩 감소
더 이상 다음이 없을 경우 다이얼로그로 목록으로 돌아가기 확인 다이얼로그 표시
이전이 없을 경우 이전 비활성화

subject, exam_session 정보를 기준으로 current_question_index를 localstorage에 저장하고
동일한 subject, exam_session 정보로 answerSheet로 진입하였을때 해당 current_question_index으로 이동

{
    "id": "jootaek1_20080907_13",
    "exam_type": "주택관리사보1차",
    "exam_session": "2008-09-07",
    "subject": "민법",
    "question_number": 13,
    "question_text": "법률행위가 유효한 것은? (다툼이 있으면 판례에 의함)",
    "choices": [
      {
        "no": 1,
        "text": "특정되어 있지 않고 특정할 수도 없는 물건을 매도한 경우"
      },
      {
        "no": 2,
        "text": "건물이 매도되었는데 계약체결 전에 전부 소실된 경우"
      },
      {
        "no": 3,
        "text": "토지가 포락(浦落)되어 원상복구를 할 수 없는데도 그 사 실을 모르고 그것을 매도한 경우"
      },
      {
        "no": 4,
        "text": "매매계약 체결 후에 매매목적물인 토지 전부가 수용되어 소유권이전이 불가능하게 된 경우"
      },
      {
        "no": 5,
        "text": "甲이 자신의 토지를 乙에게 매도한 후 丙의 대리인 丁이 甲의 배임행위에 적극 가담하여 그 토지를 이중으로 매수하였으나 丙이 그 사정을 알지 못한 경우, 甲과 丙사 이의 매매계약"
      }
    ],
    "correct_answer": 4
  },

