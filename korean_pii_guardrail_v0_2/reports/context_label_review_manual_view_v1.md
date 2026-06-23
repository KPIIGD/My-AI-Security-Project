# M4 Phase 6 Manual Label Review View

Raw-free reviewer view. Fill reviewer labels in `data/context_corpus/context_anchor_reviewer_approved_labels_v1.jsonl` after reviewing. Allowed reviewer_label values: `true_pii`, `non_pii`, `unknown`.

| no | draft_label_id | entity_group | anchor_entity | domain | lane | draft_label | left_context | right_context | reviewer_label |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | draft-biifmhlagldajioj | ADDRESS | ADDRESS_FULL | customer_support | hard_negative_corpus | non_pii | lookalike-field, service-region, service-region lookalike-field | routing-guide, non-personal-reference, routing-guide non-personal-reference |  |
| 2 | draft-gcpdchikjandgahh | ADDRESS | ADDRESS_FULL | customer_support | safe_synthetic_insertion | true_pii | 방문지, 출장, 출장 방문지 | 방문, 확인, 방문 확인 |  |
| 3 | draft-accmbmcmmmcamakc | ADDRESS | ADDRESS_FULL | ecommerce | hard_negative_corpus | non_pii | lookalike-field, delivery-zone, delivery-zone lookalike-field | notice-class, non-personal-reference, notice-class non-personal-reference |  |
| 4 | draft-bjcgnpdcajeoomff | ADDRESS | ADDRESS_FULL | ecommerce | safe_synthetic_insertion | true_pii | 배송지, 배송, 배송 배송지 | 변경, 확인, 변경 확인 |  |
| 5 | draft-fdhlnfdoadeoahof | ADDRESS | ADDRESS_UNIT | education | hard_negative_corpus | non_pii | lookalike-field, campus-zone, campus-zone lookalike-field | map-section, non-personal-reference, map-section non-personal-reference |  |
| 6 | draft-cmihcllkdmemhklj | ADDRESS | ADDRESS_FULL | education | safe_synthetic_insertion | true_pii | 거주지, 원서, 원서 거주지 | 통학, 확인, 통학 확인 |  |
| 7 | draft-obkcpjpjbdkigoaa | ADDRESS | ADDRESS_UNIT | enterprise_internal | hard_negative_corpus | non_pii | lookalike-field, work-zone, work-zone lookalike-field | assignment-rule, non-personal-reference, assignment-rule non-personal-reference |  |
| 8 | draft-doedcmmddbmlmekb | ADDRESS | ADDRESS_UNIT | enterprise_internal | safe_synthetic_insertion | true_pii | 근무지, 시설, 시설 근무지 | 배정, 확인, 배정 확인 |  |
| 9 | draft-alidmkejghbbpoad | ADDRESS | ADDRESS_UNIT | finance | hard_negative_corpus | non_pii | lookalike-field, branch-zone, branch-zone lookalike-field | desk-list, non-personal-reference, desk-list non-personal-reference |  |
| 10 | draft-nmdpandgmnjlkgad | ADDRESS | ADDRESS_FULL | finance | safe_synthetic_insertion | true_pii | 거주지, 본인, 본인 거주지 | 심사, 등록, 심사 등록 |  |
| 11 | draft-gknmdienmemhcmdf | ADDRESS | ADDRESS_FULL | healthcare | hard_negative_corpus | non_pii | lookalike-field, visit-zone, visit-zone lookalike-field | facility-guide, non-personal-reference, facility-guide non-personal-reference |  |
| 12 | draft-acppejkffdebpido | ADDRESS | ADDRESS_FULL | healthcare | safe_synthetic_insertion | true_pii | 거주지, 접수, 접수 거주지 | 확인, 기록, 확인 기록 |  |
| 13 | draft-aegnipkogcebilfp | ADDRESS | ADDRESS_FULL | public_services | hard_negative_corpus | non_pii | lookalike-field, admin-region, admin-region lookalike-field | civil-guide, non-personal-reference, civil-guide non-personal-reference |  |
| 14 | draft-ailmjaodomdjochj | ADDRESS | ADDRESS_FULL | public_services | safe_synthetic_insertion | true_pii | 주소, 민원, 민원 주소 | 발급, 검토, 발급 검토 |  |
| 15 | draft-ammggjaafjocgbld | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 문의, 구매, 구매 문의, 법인, 및 | 고객센터, 및, 고객센터 및, 물류센터, 서울특별시 |  |
| 16 | draft-bhnoecdanomkfnin | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 상담, 상담 환불 | 확인, 접수, 확인 접수 |  |
| 17 | draft-amkgcoeeechcelmk | BANK_ACCOUNT | BANK_ACCOUNT | developer_docs | public_web_context | non_pii | to, version, version to, need, upgrade |  |  |
| 18 | draft-acdgallbofddbanf | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 154차, 154차 변경일, 2019-10-18, 개인정보처리방침 | 개인정보처리방침, 153차, 개인정보처리방침 153차, 변경일, 2019-08-20 |  |
| 19 | draft-aedhbhpjcggjbipn | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 주, 바자울정보기술, 바자울정보기술 주, 통합연구관리, 시스템 |  |  |
| 20 | draft-pnpobbgfhffhlpnm | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | public_web_context | non_pii | 팩스번호, /, / 팩스번호, 1899-9100, 지역선택 | 개인정보처리방침, 이용약관, 개인정보처리방침 이용약관, Copyright, © |  |
| 21 | draft-aammdljncemeoglo | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 22 | draft-anmdiehifjdhgofe | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | kr, or, or kr, http, //www | 새마을금고, ○, 새마을금고 ○, https, //ibs |  |
| 23 | draft-abmoonmkknkeehfl | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 24 | draft-bkiamgododogjcbj | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 122, 636, 636 122, 812, 699 | 127, 625, 127 625, 130, 500 |  |
| 25 | draft-afbbhbgeckpfjdmp | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 연락처, 예약일, 예약일 연락처, 온라인예약, 취소하기 | 019, -, 019 -, 예약취소, 신청 |  |
| 26 | draft-bpnmcejjfnnkjhag | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 예약, 예약 환불 | 확인, 접수, 확인 접수 |  |
| 27 | draft-bkmheeckchmjdelh | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2026-01-26 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 28 | draft-aplakefppcnkiadi | BANK_ACCOUNT | BANK_ACCOUNT | public_services | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 민원, 민원 환불 | 확인, 발급, 확인 발급 |  |
| 29 | draft-aiioacpjcclfbmmh | EMAIL | EMAIL | customer_support | public_web_context | non_pii | E-mail, Fax, Fax E-mail, 아이에스비즈타워, Tel | 통신판매업신고, 2013-서울금천-0836호, 통신판매업신고 2013-서울금천-0836호, 개인정보, 보호배상 |  |
| 30 | draft-annolcggcpboomfi | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 상담, 상담 인증 | 발송, 접수, 발송 접수 |  |
| 31 | draft-djcldhkamannfjfm | EMAIL | EMAIL | developer_docs | public_web_context | non_pii | buyer_email, 1004, 1004 buyer_email, 주문명, 결제테스트 | buyer_name, 구매자이름, buyer_name 구매자이름, buyer_tel, // |  |
| 32 | draft-afnhcolljgjembka | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 안병근, 개인정보관리책임자, 개인정보관리책임자 안병근, 원효로3가, 지피클럽 | ⓒ, 제이플리, ⓒ 제이플리, All, rights |  |
| 33 | draft-adbkidjfokcaadge | EMAIL | EMAIL | education | public_web_context | non_pii | -, kr, kr -, ac, - - | -, ac, - ac, kr, 붙임 |  |
| 34 | draft-aphnjklpkenkmkog | EMAIL | EMAIL | education | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 등록, 등록 인증 | 발송, 신청, 발송 신청 |  |
| 35 | draft-abbenpeiapocccjg | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 요청, 요청 인증 | 발송, 승인, 발송 승인 |  |
| 36 | draft-cnbppdfkbndicflj | EMAIL | EMAIL | finance | public_web_context | non_pii | E-mail, /, / E-mail, TEL, FAX | 46004, 부산광역시, 46004 부산광역시, 기장군, 정관읍 |  |
| 37 | draft-amakbkmjdndpnagk | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 환불, 안내 | 확인, 심사, 확인 심사 |  |
| 38 | draft-ahnoehjlnikjhilk | EMAIL | EMAIL | general_web | public_web_context | non_pii | E-Mail, 연락처, 연락처 E-Mail, 장남수, 직위 | 성명, 박희순, 성명 박희순, 주민성, 직위 |  |
| 39 | draft-ahoalfcimpcmmoga | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 책임자, 책임자 이메일, 전화번호, 02 | 2, 정보주체는, 2 정보주체는, 병원의, 서비스를 |  |
| 40 | draft-aejgpfeghjkkhfno | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, ·, · 이메일, 전화, 팩스 | 조사총괄과, -, 조사총괄과 -, 유출신고, 신고 |  |
| 41 | draft-eacfbkfcbenngaia | PERSON_NAME | PERSON_NAME | customer_support | hard_negative_corpus | non_pii | lookalike-field, product-name, product-name lookalike-field | support-category, non-personal-reference, support-category non-personal-reference |  |
| 42 | draft-caljajncakjkkngb | PERSON_NAME | PERSON_NAME | customer_support | safe_synthetic_insertion | true_pii | 고객명, 문의자, 문의자 고객명 | 확인, 상담, 확인 상담 |  |
| 43 | draft-ojppibdpbpefpjei | PERSON_NAME | PERSON_NAME | ecommerce | hard_negative_corpus | non_pii | lookalike-field, brand-name, brand-name lookalike-field | option-guide, non-personal-reference, option-guide non-personal-reference |  |
| 44 | draft-kdjnhfjonnidmdcb | PERSON_NAME | PERSON_NAME | ecommerce | safe_synthetic_insertion | true_pii | 수령인, 배송, 배송 수령인 | 확인, 입력, 확인 입력 |  |
| 45 | draft-cjlmppgbdpieamhb | PERSON_NAME | PERSON_NAME | education | hard_negative_corpus | non_pii | lookalike-field, course-name, course-name lookalike-field | enrollment-flow, non-personal-reference, enrollment-flow non-personal-reference |  |
| 46 | draft-ondibikjlmpkpfdh | PERSON_NAME | PERSON_NAME | education | safe_synthetic_insertion | true_pii | 학생명, 신청, 신청 학생명 | 학적, 접수, 학적 접수 |  |
| 47 | draft-baemhfphgflimhni | PERSON_NAME | PERSON_NAME | enterprise_internal | hard_negative_corpus | non_pii | lookalike-field, project-name, project-name lookalike-field | approval-flow, non-personal-reference, approval-flow non-personal-reference |  |
| 48 | draft-jkjoililnnejmpcp | PERSON_NAME | PERSON_NAME | enterprise_internal | safe_synthetic_insertion | true_pii | 직원명, 요청, 요청 직원명 | 처리, 부서, 처리 부서 |  |
| 49 | draft-ofakdpalcjdcmeag | PERSON_NAME | PERSON_NAME | finance | hard_negative_corpus | non_pii | lookalike-field, fund-name, fund-name lookalike-field | product-class, non-personal-reference, product-class non-personal-reference |  |
| 50 | draft-hpbfccjddgnbecpp | PERSON_NAME | PERSON_NAME | finance | safe_synthetic_insertion | true_pii | 예금주, 환불, 환불 예금주 | 인증, 확인, 인증 확인 |  |
| 51 | draft-bifmgmcjfhgnkedh | PERSON_NAME | PERSON_NAME | healthcare | hard_negative_corpus | non_pii | lookalike-field, department-name, department-name lookalike-field | clinic-guide, non-personal-reference, clinic-guide non-personal-reference |  |
| 52 | draft-ppjpnkeehaiiaggm | PERSON_NAME | PERSON_NAME | healthcare | safe_synthetic_insertion | true_pii | 환자명, 예약, 예약 환자명 | 진료, 확인, 진료 확인 |  |
| 53 | draft-aogokmfaoophiegl | PERSON_NAME | PERSON_NAME | public_services | hard_negative_corpus | non_pii | lookalike-field, office-name, office-name lookalike-field | petition-class, non-personal-reference, petition-class non-personal-reference |  |
| 54 | draft-omofocejanpekdef | PERSON_NAME | PERSON_NAME | public_services | safe_synthetic_insertion | true_pii | 민원인, 민원, 민원 민원인 | 발급, 검토, 발급 검토 |  |
| 55 | draft-cddfabjmkekcppfj | PHONE | PHONE_LANDLINE | customer_support | public_web_context | non_pii | 전화, kr, kr 전화, //www, spo | 경찰청, 사이버테러대응센터, 경찰청 사이버테러대응센터, http, //www |  |
| 56 | draft-aephnhmddmicncla | PHONE | PHONE_LANDLINE | developer_docs | public_web_context | non_pii | buyer_tel, 포트원, 포트원 buyer_tel, buyer_email, io | m_redirect_url, 모바일에서, m_redirect_url 모바일에서, 결제, 완료 |  |
| 57 | draft-aakmfbbmpknkobmd | PHONE | PHONE_MOBILE | ecommerce | public_web_context | non_pii | 문자, 채널, 채널 문자, 웹, 24시 | 문자, 전용, 문자 전용, 전화, 1600-0103 |  |
| 58 | draft-abejfmbfcfcnlfne | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 연락처, -, - 연락처, 책임자, 총무관리처장 | -, 부, - 부, 서, 총무관리처 |  |
| 59 | draft-fiaeahedflkmflkg | PHONE | PHONE_LANDLINE | enterprise_internal | public_web_context | non_pii | 예 | 수습직원을, 관리하는, 수습직원을 관리하는, 경우에는, 수습여부를 |  |
| 60 | draft-aglpebkadicpinoa | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 대표전화, 30, 30 대표전화, 서울시, 중구 | 고객센터, 1588-0037, 고객센터 1588-0037, 팩스, Copyright |  |
| 61 | draft-adkddaikohbkejgm | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 경영지원팀, 한국문화기술기획평가원, 한국문화기술기획평가원 경영지원팀, CKL기업지원센터, 기업육성팀 | 콘텐츠수출마케팅플랫폼, 수출전략팀, 콘텐츠수출마케팅플랫폼 수출전략팀, 한국콘텐츠아카데미, 인재양성팀 |  |
| 62 | draft-aaekcpfmlpjhodcp | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | --, 병문안시간, 병문안시간 --, 협력병·의원, 입찰공고 | =, --, = --, 14353, 경기도 |  |
| 63 | draft-addpnmejcklaobln | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 엑스, 카카오스토리 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 64 | draft-clllogmenkimohln | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | customer_support | public_web_context | non_pii | 사업자등록번호, KOREAN, KOREAN 사업자등록번호, 서비스소개, FAMILY | 원격지원, 서비스, 원격지원 서비스, ※, 원격지원이 |  |
| 65 | draft-amgoaidfecjdecjg | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | developer_docs | public_web_context | non_pii | iat, 1d61d6c8-173b-488c-b8af-2e2b6ca29777, 1d61d6c8-173b-488c-b8af-2e2b6ca29777 iat, kakao, com | jti, 7185208e-c045-41e9-a2ff-0b219b9e123e, jti 7185208e-c045-41e9-a2ff-0b219b9e123e, events, https |  |
| 66 | draft-admggeldmijmbffd | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 노태문, 노태문 사업자등록번호, 주식회사, 대표이사 | 사업자, 정보확인, 사업자 정보확인, 통신판매업신고번호, 2000-경기수원-0515 |  |
| 67 | draft-apcapaeheflolick | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | education | public_web_context | non_pii | 고유번호, 제2014-서울강북-0056, 제2014-서울강북-0056 고유번호, 60, 미아동 | ㅣ, 총장, ㅣ 총장, 이은주, 대표전화 |  |
| 68 | draft-bfpkgcbdhgcbednd | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | enterprise_internal | public_web_context | non_pii | 사업자등록번호, 등록한, 등록한 사업자등록번호, 클릭하면, 현재 | 으로, 기, 으로 기, 입력한, 전표입력의 |  |
| 69 | draft-bhpglhdbiojoacpi | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | finance | public_web_context | non_pii | 사업자등록번호, 738-3000, 738-3000 사업자등록번호, 10, TEL | Copyright, ©, Copyright ©, 2020, Korea |  |
| 70 | draft-deekfblijjbdiacj | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | general_web | public_web_context | non_pii | f, 65535, 65535 f, xref, 0 | 00000, n, 00000 n, n 00000, 00000 n 00000 |  |
| 71 | draft-clinjgjapplhhajo | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 등록번호, 사업자, 사업자 등록번호, 법인명, 서울특별시 | 대표자, 이현석, 대표자 이현석, copyright, by |  |
| 72 | draft-apmchcmpokoinoki | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 국민, 입금계좌정보, 입금계좌정보 국민, 00, 주말/공휴일 | 농협, PC버전, 농협 PC버전, 상점정보, 이용안내 |  |
| 73 | draft-cmkfafblpdmlffnf | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 상담, 처리 상담 |  |
| 74 | draft-cbbmocjingncojoa | BANK_ACCOUNT | BANK_ACCOUNT | developer_docs | public_web_context | non_pii | 사용하려면, API를, API를 사용하려면, 400, API_VERSION_UPDATE_NEEDED | 이상의, 버전을, 이상의 버전을, 사용해야, 합니다 |  |
| 75 | draft-adohhdnbgjmpgeeh | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 제정, /, / 제정, 플라시스템, 시행일 | /, 버전, / 버전, 2, 0 |  |
| 76 | draft-akmocajkfelabhdo | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 24, 23, 23 24, 20, 21 | 30, 31, 30 31, 일, 성별 |  |
| 77 | draft-abnpfcmfnaeikcac | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 78 | draft-bpgemnfmpbmpcael | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 전화번호, com, com 전화번호, co, kr | 042, 043, 042 043, 044, 051 |  |
| 79 | draft-bolgdnjafcjbjhfk | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 80 | draft-ckeokdkbaepdgcck | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 83, 500, 500 83, 283, 375 | 574, 574 574 |  |
| 81 | draft-efpjaeeplbbbcboo | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 등, 약물용량, 약물용량 등, 신장, 체중 | 경보제약, 2024-12-04, 경보제약 2024-12-04, 수술, 후 |  |
| 82 | draft-cfidaecdphjnamng | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 예약, 처리 예약 |  |
| 83 | draft-cgjjfdgikabgeeid | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2025-12-12 |  |
| 84 | draft-eccigpoillglcpbl | BANK_ACCOUNT | BANK_ACCOUNT | public_services | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 발급, 입금 | 처리, 민원, 처리 민원 |  |
| 85 | draft-bhpbcgcnkdmcdnga | EMAIL | EMAIL | customer_support | public_web_context | non_pii | /, 운영팀장, 운영팀장 /, 관리담당자, 김숙희 | 귀하께서는, 회사의, 귀하께서는 회사의, 서비스를, 이용하시며 |  |
| 86 | draft-bbjcfeifhmnpbiid | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 접수, 안내 | 확인, 상담, 확인 상담 |  |
| 87 | draft-ekjjdiepcppcmokl | EMAIL | EMAIL | developer_docs | public_web_context | non_pii | buyer_email, USD, USD buyer_email, //, 기본값 | buyer_name, 구매자이름, buyer_name 구매자이름, buyer_tel, buyer_addr |  |
| 88 | draft-agaibggagfjopple | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 1600-0455, 1600-0455 이메일, 소속, 대표 | -, 개인정보, - 개인정보, 보호담당자, 성명 |  |
| 89 | draft-afhfahnpabmdpjep | EMAIL | EMAIL | education | public_web_context | non_pii | 이메일, 전화번호, 전화번호 이메일, 장, 중 | 개인정보, 분야별, 개인정보 분야별, 책임자, 본교는 |  |
| 90 | draft-bbnbklcckdpmfgpg | EMAIL | EMAIL | education | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 등록, 등록 인증 | 발송, 신청, 발송 신청 |  |
| 91 | draft-bdjehedkfamkheob | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 92 | draft-jlghifnhnmhpmkjh | EMAIL | EMAIL | finance | public_web_context | non_pii | E-mail, FAX, FAX E-mail, 42-15, TEL | COPYRIGHT, C, COPYRIGHT C, 기장장애인복지관, C 기장장애인복지관 |  |
| 93 | draft-blicodoflmlpnnlj | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 94 | draft-anofdebpmfngnioc | EMAIL | EMAIL | general_web | public_web_context | non_pii | 팀원, 대학원교학팀, 대학원교학팀 팀원, 대학원, 교학처 | 대학원, 입시, 대학원 입시, 학적관리, 학사관리 |  |
| 95 | draft-akcjdnbbfcanlahf | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 책임자, 책임자 이메일, 전화번호, 02 | 연구관제관리시스템, 개인정보, 연구관제관리시스템 개인정보, 관리, 부서 |  |
| 96 | draft-alpogdhkgfjbodei | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, ·, · 이메일, 전화, 팩스 | 개인정보, 보호정책과, 개인정보 보호정책과, -, 지우개 |  |
| 97 | draft-hiobdgngfaamlidg | PHONE | PHONE_LANDLINE | customer_support | public_web_context | non_pii | TEL, 출판문화정보산업단지, 출판문화정보산업단지 TEL, 파주시, 문발로 | FAX, 대표이사, FAX 대표이사, 이종춘, 개인정보관리자 |  |
| 98 | draft-alkojdfecbebkcae | PHONE | PHONE_MOBILE | developer_docs | public_web_context | non_pii | buyer_tel, 구매자이름, 구매자이름 buyer_tel, buyer_email, io | //, 필수, // 필수, buyer_addr, 서울특별시 |  |
| 99 | draft-ajhlibbolifkapgh | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 전화번호, 사업본부, 사업본부 전화번호, 소속, 온라인 | 이메일, co, 이메일 co, kr, o |  |
| 100 | draft-adcgkclcpblelgmf | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 문의, ✱전화, ✱전화 문의, 총무팀, 개인정보보호 | ✱이메일, ac, ✱이메일 ac, kr, - |  |
| 101 | draft-baaemimlpipjopga | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | kr, co, co kr, http, //www | IBK투자증권, ○, IBK투자증권 ○, X, http |  |
| 102 | draft-ahnidhhpmcpipoah | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 전화, 전화 전화, 성명, 강한승, 부장 | 팩스, 주소, 팩스 주소, 전라남도, 나주시 |  |
| 103 | draft-aakehdgieddmbnae | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 약처방문의, 건강검진예약, 건강검진예약 약처방문의, 1599-3114, 진료예약 | ~8, 약처방전재발급, ~8 약처방전재발급, 입원비확인ARS, 응급실 |  |
| 104 | draft-agohogielcddbpam | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 연락처, 권구열, 권구열 연락처, 개인정보보호, 담당자 | kr, 정보주체께서는, kr 정보주체께서는, 국가민방위재난안전교육원의, 서비스를 |  |
| 105 | draft-djjoknlmkiflealj | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | customer_support | public_web_context | non_pii | 등록번호, 사업자, 사업자 등록번호, 보호, 책임자 | 통신판매업신고번호, 2014-서울중랑-0456호, 통신판매업신고번호 2014-서울중랑-0456호, 전화, 1666-4327 |  |
| 106 | draft-bnflonphheopecho | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 김재연, 김재연 사업자등록번호, 126, 407호 | 통신판매업신고번호, 2025-경기김포-7398, 통신판매업신고번호 2025-경기김포-7398, 개인정보보호책임자, 박준태 |  |
| 107 | draft-dddhkfjildmajbjf | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | education | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, Fax, 대표 | /, 통신판매업신고번호, / 통신판매업신고번호, 제2014-서울동대문-0532호, 사이버한국외국어대학교 |  |
| 108 | draft-fjlphemcdfapnkka | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | enterprise_internal | public_web_context | non_pii | 사업자등록번호, 에, 에 사업자등록번호, 예시, 거래처등록 | 로, 초기, 로 초기, 입력, 매입매출전표입력 |  |
| 109 | draft-egnigclhgpmgpgme | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | finance | public_web_context | non_pii | 등록번호, 사업자, 사업자 등록번호, 제휴문의, KB스타뱅킹 | 서울특별시, 영등포구, 서울특별시 영등포구, 국제금융로8길, 26 |  |
| 110 | draft-dflgfdbpjdkpgijl | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | general_web | public_web_context | non_pii | n, 00000, 00000 n, 23, 65535 | 00000, n, 00000 n, n 00000, 00000 n 00000 |  |
| 111 | draft-ddicmgnjejnahgpg | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 사업자등록번호, kr, kr 사업자등록번호, 채동완, 이메일 | COPYRIGHTⓒ, 2023, COPYRIGHTⓒ 2023, by, Seoul |  |
| 112 | draft-blgiippabaleagnl | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | FAQ, 모음, 모음 FAQ, 이벤트, 상품후기 | ~17시, 12~13시반, ~17시 12~13시반, 점심, 주말/공휴일 |  |
| 113 | draft-denggbjdpmnnodfk | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 상담, 처리 상담 |  |
| 114 | draft-ddiepknkeockkejl | BANK_ACCOUNT | BANK_ACCOUNT | developer_docs | public_web_context | non_pii | 들어, 예를, 예를 들어 | T00, 00, T00 00, 으로, 설정하면 |  |
| 115 | draft-affakkdakhnokbjn | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 방침은, 본, 본 방침은, 개인정보, 처리방침 | 부터, 시행합니다, 부터 시행합니다 |  |
| 116 | draft-bakooifkbbciljbl | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 자가조치방법, 시험, 시험 자가조치방법, 재신청, 2026-01-16 | 시험, 메뉴얼, 시험 메뉴얼, 2019-03-19, 수강료 |  |
| 117 | draft-adhhlmoaccihhlki | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 118 | draft-cadajfgeienkjbba | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 052, 051, 051 052, 042, 043 | 063, 064, 063 064, 070, 휴대전화 |  |
| 119 | draft-cdfdhhkhhfbpkjhi | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 120 | draft-dojmgajdhogimmlg | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 없음, 31, 31 없음, ~, 2027 | 이행, ②, 이행 ②, 콘진원은, 위탁계약 |  |
| 121 | draft-eoocfpdjhemnijjg | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 제-, EMR, EMR 제-, 11, 03 | 09, 30, 09 30, ~, 2026 |  |
| 122 | draft-dimhiepnedgnhjmh | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 예약, 예약 환불 | 확인, 접수, 확인 접수 |  |
| 123 | draft-dccflbigkejekggj | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2024-07-29 |  |
| 124 | draft-gmjncbfhagpjgfbm | BANK_ACCOUNT | BANK_ACCOUNT | public_services | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 민원, 민원 환불 | 확인, 발급, 확인 발급 |  |
| 125 | draft-eomodfmafiekpbgb | EMAIL | EMAIL | customer_support | public_web_context | non_pii | /, 연락처, 연락처 /, 성영주, 본부장 | •, 주소, • 주소, 대구광역시, 수성구 |  |
| 126 | draft-bhedbaeenccmfkpn | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 상담, 상담 인증 | 발송, 접수, 발송 접수 |  |
| 127 | draft-fnmpbeafcmfmkbna | EMAIL | EMAIL | developer_docs | public_web_context | non_pii | buyer_email, KRW, KRW buyer_email, 14, 2 | buyer_name, 구매자이름, buyer_name 구매자이름, buyer_tel, buyer_addr |  |
| 128 | draft-agckkhonflcgcene | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | E-mail, com, com E-mail, 개인정보보호책임자, 주식회사 | 형식으로, 수정해주세요, 형식으로 수정해주세요 |  |
| 129 | draft-bfdenlkmhkhaiodf | EMAIL | EMAIL | education | public_web_context | non_pii | -, - -, 032, 835-9528, 이메일 | -, ac, - ac, kr, ac kr |  |
| 130 | draft-bganhjedmoacinel | EMAIL | EMAIL | education | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 등록, 등록 인증 | 발송, 신청, 발송 신청 |  |
| 131 | draft-boaicjdpjejaebfi | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 132 | draft-olfnjnmkinkkcaoj | EMAIL | EMAIL | finance | public_web_context | non_pii | 문의, 메일, 메일 문의, 전담, 지원센터 | 카톡, 문의, 카톡 문의, 근로자휴가지원, Family |  |
| 133 | draft-cjlffmfmlbdmgljp | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 134 | draft-cbjobnhfbccbfflc | EMAIL | EMAIL | general_web | public_web_context | non_pii |  | ②, 정보주체는, ② 정보주체는, 개인정보, 침해로 |  |
| 135 | draft-bfofagmacmehkbej | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 연락처, 연락처 이메일, 소, 속 | 개인정보, 열람, 개인정보 열람, 담당자, 성 |  |
| 136 | draft-cpcafedpijfdjomb | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, -, - 이메일, 전화, 팩스 | 목차, 개인정보처리방침은, 목차 개인정보처리방침은, 다음과, 같은내용으로 |  |
| 137 | draft-hippobgphnmjcagn | PHONE | PHONE_LANDLINE | customer_support | public_web_context | non_pii | Tel, 2층, 2층 Tel, 12, 이문리 | Copyright, ©, Copyright ©, 경북외국인노동자상담센터, all |  |
| 138 | draft-hioncemmankbkfci | PHONE | PHONE_MOBILE | developer_docs | public_web_context | non_pii | buyer_tel, 구매자이름, 구매자이름 buyer_tel, buyer_email, io | buyer_addr, 서울특별시, buyer_addr 서울특별시, 강남구, 삼성동 |  |
| 139 | draft-apmncopbjgmndbjf | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 전화번호, net, net 전화번호, 담당자, 정연종 | 제9조, 개인정보, 제9조 개인정보, 보호책임자, 및 |  |
| 140 | draft-aiahafcelnacmgic | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | ㈜다몬미디어, 대행, 대행 ㈜다몬미디어, 중앙도서관, 교외접속시스템 | 2026 |  |
| 141 | draft-baofakdniiiihnnj | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 팩스번호, 전화번호, 전화번호 팩스번호, 119, 하광교동 | 당직실, 1918, 당직실 1918, 찾아오시는, 길 |  |
| 142 | draft-anlkdlgcbmjmlfbm | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | FAX, 통해, 통해 FAX, 이내, 아래의 | 또는, 이메일, 또는 이메일, co, kr |  |
| 143 | draft-aclahlidfccinegk | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | ☎ | Q, 결제가, Q 결제가, 안, 되는 |  |
| 144 | draft-akfmccagihojnegl | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 태현수, 가명정보, 가명정보 태현수, 권리, 김직동 | 자율보호정책과장, 열람요구, 자율보호정책과장 열람요구, 정보주체, 권리행사 |  |
| 145 | draft-ebkebklhpgjialfi | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | customer_support | public_web_context | non_pii | 사업자등록번호, 양우진, 양우진 사업자등록번호, 대표자, 장승웅 | 고객센터, 1588-2336, 고객센터 1588-2336, 통신판매업신고, 제2014-서울강남-00193호 |  |
| 146 | draft-ciehlohmjmodbpcg | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 김정웅, 김정웅 사업자등록번호, 주, 지피클럽 | 통신판매업신고번호, 2018-서울마포-0573호, 통신판매업신고번호 2018-서울마포-0573호, 사업자정보확인, 고객센터 |  |
| 147 | draft-dmfmpdbmchmeglag | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | education | public_web_context | non_pii | 사업자번호, ｜, ｜ 사업자번호, 대표자, 이재민 | 대표전화, ｜, 대표전화 ｜, 입시문의, Copyright |  |
| 148 | draft-gjijgealdofebemj | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | enterprise_internal | public_web_context | non_pii | 그대로, 데이터값, 데이터값 그대로, 전표입력의, 사업자등록번호는 | 로, 유지됩니다, 로 유지됩니다 |  |
| 149 | draft-eliidoplnbniialk | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | finance | public_web_context | non_pii | 중견기업, 활동지원센터, 활동지원센터 중견기업, 연합회, 양주시지회 | 2018, 2019, 2018 2019, 2020, 2022 |  |
| 150 | draft-fahphpejddjhmhjo | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | general_web | public_web_context | non_pii | n, 00000, 00000 n, n 00000, n 00000 n | 00000, n, 00000 n, trailer, n 00000 |  |
| 151 | draft-ddnhdcglokkkafbb | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, 대표전화, 1599-3114 | 박승우, copyright©1996-2015, 박승우 copyright©1996-2015, by, Samsung |  |
| 152 | draft-cdomnejoffbijhlk | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 수신자부담무료전화, 1588-2336, 1588-2336 수신자부담무료전화, 전자우편, com | 기타, 개인정보침해에, 기타 개인정보침해에, 대한, 신고나 |  |
| 153 | draft-efngidficdaiojdb | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 상담, 처리 상담 |  |
| 154 | draft-afghenodmcofapcg | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 고객상담, 마곡동, 마곡동 고객상담, 강서구, 마곡중앙8로5길 | /, 전자우편, / 전자우편, org, Copyright |  |
| 155 | draft-bdkimngmkmalnmlf | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 수정일, 최종, 최종 수정일, 연락처, 총무과 | 주요서비스, 교무회의방송, 주요서비스 교무회의방송, 교수채용, 인터넷증명 |  |
| 156 | draft-aklcjphecpibpend | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 157 | draft-dobjakohcabgmamk | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | KB드림톡적금, 골든라이프뱅킹, 골든라이프뱅킹 KB드림톡적금, 퇴직연금, -- | --, 자동이체통합관리, -- 자동이체통합관리, 2018-11-12, 보안센터 |  |
| 158 | draft-cgignkhaakgodajj | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 159 | draft-efbijdegeanfjpie | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 없음, 31, 31 없음, ~, 2027 | 예정, 닫기, 예정 닫기, 레이어팝업닫기, 개인정보의 |  |
| 160 | draft-fempjggfkphpfmog | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 제-, EMR, EMR 제-, 11, 03 | 09, 30, 09 30, ~, 2026 |  |
| 161 | draft-dmfofkanpfalaoli | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 예약, 예약 환불 | 확인, 접수, 확인 접수 |  |
| 162 | draft-dohkamiikmgmblef | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2025-10-29 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 163 | draft-iggnbmlppemiacae | BANK_ACCOUNT | BANK_ACCOUNT | public_services | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 민원, 민원 환불 | 확인, 발급, 확인 발급 |  |
| 164 | draft-fbjpicegggjggcgj | EMAIL | EMAIL | customer_support | public_web_context | non_pii | 전자우편, 팀장, 팀장 전자우편, 양우진, 직 | 문의전화, 1588-2336, 문의전화 1588-2336, 전자우편, com |  |
| 165 | draft-enbaedicenbnilpb | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 상담, 상담 인증 | 발송, 접수, 발송 접수 |  |
| 166 | draft-jekjdghefdmdajkc | EMAIL | EMAIL | developer_docs | public_web_context | non_pii | 1544-7772, 고객센터, 고객센터 1544-7772, 토스페이먼츠, 토스페이먼츠 고객센터 | 로, 문의해주세요, 로 문의해주세요 |  |
| 167 | draft-agegcbmfeoneianh | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 전화번호, 전화번호 이메일, PL, 소속 | 제10조 |  |
| 168 | draft-camfcbpdhipgjbkf | EMAIL | EMAIL | education | public_web_context | non_pii | ✱이메일, 문의, 문의 ✱이메일, 개인정보보호, 담당자 | -, 접수처로, - 접수처로, 연락을, 주시면 |  |
| 169 | draft-gaebkhggcdpgpfjk | EMAIL | EMAIL | education | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 등록, 등록 인증 | 발송, 신청, 발송 신청 |  |
| 170 | draft-cnejebifmaflamda | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 171 | draft-ckkpopplngbhbodf | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 172 | draft-cciodepglilimepn | EMAIL | EMAIL | general_web | public_web_context | non_pii | 이메일, 김철홍, 김철홍 이메일, 고객센터, 개인정보보호책임자 | 9 |  |
| 173 | draft-bgpakpigjcjldeek | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, -, - 이메일, 전화번호, 032 | ※, 자세한, ※ 자세한, 내용은, 개인정보 |  |
| 174 | draft-dnjkhaffddepohin | EMAIL | EMAIL | public_services | public_web_context | non_pii | 연락처, 기획협력과, 기획협력과 연락처, 및, 신고 | ③, 「개인정보, ③ 「개인정보, 보호법」, 제35조 |  |
| 175 | draft-icdlgceagoocbcgg | PHONE | PHONE_LANDLINE | customer_support | public_web_context | non_pii | FAX, 2015-서울강남-01654호, 2015-서울강남-01654호 FAX, 최상길, 통신판매업신고 | 이메일, co, 이메일 co, kr, Copyright |  |
| 176 | draft-bhbojfmhbnkkbpbd | PHONE | PHONE_MOBILE | ecommerce | public_web_context | non_pii | 문자, 채널, 채널 문자, 웹, 24시 | 문자, 전용, 문자 전용, 전화, 1600-0103 |  |
| 177 | draft-aidhhhcopmadkdjf | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 입학관리팀, 유지보수, 유지보수 입학관리팀, 대행, 입학전형 | 5, 교육수요자만족도조사, 5 교육수요자만족도조사, ㈜글로벌리서치, 교육수요자인 |  |
| 178 | draft-bjjefhhhenoheilc | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 팩스, 1588-0037, 1588-0037 팩스, 30, 대표전화 | Copyright, c, Copyright c, KDIC, All |  |
| 179 | draft-bdgeoehpihdmkmog | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 과장, 최그린, 최그린 과장, 사서, 게임더하기 | ③, 정보주체는, ③ 정보주체는, 제1항의, 열람청구 |  |
| 180 | draft-adkcnhlimmakfjab | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 전화예약번호 | 진료예약, 바로가기, 진료예약 바로가기, 담당부서, 원무팀 |  |
| 181 | draft-almikginecedogmj | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 팩스, ·, · 팩스, 정윤식, 전화 | ·, 이메일, · 이메일, kr, 조사총괄과 |  |
| 182 | draft-fjgkkhpennofcjmg | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | customer_support | public_web_context | non_pii | 사업자등록번호, 최상길, 최상길 사업자등록번호, 111길, 11 | 개인정보관리책임자, 최상길, 개인정보관리책임자 최상길, 통신판매업신고, 제 |  |
| 183 | draft-cnlogoligkhbnofb | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 등록번호, 사업자, 사업자 등록번호, 통신판매업신고번호, 제 | 주식회사, 플라시스템, 주식회사 플라시스템, All, Right |  |
| 184 | draft-egokmalgjoaodggp | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | education | public_web_context | non_pii | 사업자등록번호, FAX, FAX 사업자등록번호, 원광디지털대학교, TEL | 대표, 김윤철, 대표 김윤철, Copyright, C |  |
| 185 | draft-koeolfhabhcijakc | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | enterprise_internal | public_web_context | non_pii | 사업자등록번호, 에, 에 사업자등록번호, 초기, 입력 | 로, 전표입력, 로 전표입력, 이후, 거래처등록 |  |
| 186 | draft-nodbeenjdaighbdh | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | finance | public_web_context | non_pii | 사업자번호, 중견기업, 중견기업 사업자번호, 장애인, 활동지원센터 | 참여년도, 2018, 참여년도 2018, 2019, 2020 |  |
| 187 | draft-fgeifemkhbfhkagc | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | general_web | public_web_context | non_pii | 사업자등록번호, 한국콘텐츠진흥원, 한국콘텐츠진흥원 사업자등록번호, 35, 빛가람동 | /, 대표번호, / 대표번호, 1566-1114, Copyright |  |
| 188 | draft-djiedcbnenineilm | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, 대표전화, 1599-3114 | 박승우, copyright©1996-2015, 박승우 copyright©1996-2015, by, Samsung |  |
| 189 | draft-chaleifddfbpnajb | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 기업, ACCOUNT, ACCOUNT 기업, 고객센터, 연결하기 | 예금주, 주, 예금주 주, 제이에스벤처스, Q&A |  |
| 190 | draft-gfficegaaiibjbib | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 상담, 처리 상담 |  |
| 191 | draft-agdkkokalmemjomk | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 180차, 180차 변경일, 2021-12-15, 개인정보처리방침 | 개인정보처리방침, 179차, 개인정보처리방침 179차, 변경일, 2021-10-22 |  |
| 192 | draft-behoijojffpkkgpp | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 1980, 1981, 1981 1980, 1984, 1983 | 1974, 1973, 1974 1973, 1972, 1971 |  |
| 193 | draft-anhfaighpmaidomc | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 194 | draft-fadgckjjochdngaf | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 연락처, -, - 연락처, 070, 080 | 031, 032, 031 032, 033, 041 |  |
| 195 | draft-dicebkddlfhonbef | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 입금, 환불 입금 | 처리, 심사, 처리 심사 |  |
| 196 | draft-egnhhhcaclpnhfim | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 574, 416, 416 574, 333, 625 | 574, 574 574, 333, 574 333 |  |
| 197 | draft-fhfhilbamdoopbfg | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | --, *, * --, 전화번호, 필수 | 019, -, 019 -, --, - -- |  |
| 198 | draft-fbnpgcgacpjnllke | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 예약, 예약 환불 | 확인, 접수, 확인 접수 |  |
| 199 | draft-donbedlkhknmonbj | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2016-10-05 |  |
| 200 | draft-ipgnhljaajonpjgi | BANK_ACCOUNT | BANK_ACCOUNT | public_services | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 민원, 민원 환불 | 확인, 발급, 확인 발급 |  |
| 201 | draft-fnbnbpinmkifohfo | EMAIL | EMAIL | customer_support | public_web_context | non_pii | 이메일, 1551-9322, 1551-9322 이메일, 2동, 구산동260-34 | 통신판매업신고번호, 2024-고양일산서-0725호, 통신판매업신고번호 2024-고양일산서-0725호, copyright, 2024-고양일산서-0725호 copyright |  |
| 202 | draft-gjfhjidmjlljcmeb | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 접수, 안내 | 확인, 상담, 확인 상담 |  |
| 203 | draft-lmjnikoagjfcofha | EMAIL | EMAIL | developer_docs | public_web_context | non_pii | buyer_email | buyer_name, 포트원, buyer_name 포트원, buyer_tel, m_redirect_url |  |
| 204 | draft-ahpodlbmaebendgg | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 문의처, –, – 문의처, 전화, 1588-4730 | 3, 기타, 3 기타, 기관, 개인정보 |  |
| 205 | draft-debgblhmeejagidf | EMAIL | EMAIL | education | public_web_context | non_pii | 조성호, 총무팀, 총무팀 조성호, 이메일, 팩스 | 제6조, 개인정보의, 제6조 개인정보의, 파기, ① |  |
| 206 | draft-iehlifhipdanhbch | EMAIL | EMAIL | education | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 등록, 등록 인증 | 발송, 신청, 발송 신청 |  |
| 207 | draft-dffaogjdmmdmdkbo | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 요청, 요청 인증 | 발송, 승인, 발송 승인 |  |
| 208 | draft-cpkbhnjlaodhfcin | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 209 | draft-cjfbhlkkamdmioaj | EMAIL | EMAIL | general_web | public_web_context | non_pii | 6314 | 여기가, 고충처리부서인, 여기가 고충처리부서인, 거죠, 고충처리부서인 거죠 |  |
| 210 | draft-bkgknnkdeplnamoh | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 채동완, 채동완 이메일, 9, 대표전화 | 사업자등록번호, COPYRIGHTⓒ, 사업자등록번호 COPYRIGHTⓒ, 2023, by |  |
| 211 | draft-dnmedfbfjiheffli | EMAIL | EMAIL | public_services | public_web_context | non_pii | 전자우편, 전화, 전화 전자우편 | 개인정보보호, 담당자, 개인정보보호 담당자, 기획협력과, 박상연 |  |
| 212 | draft-ijbgfngecigfbpgb | PHONE | PHONE_LANDLINE | customer_support | public_web_context | non_pii | 전화, kr, kr 전화, //www, ctrc | 경찰청, http, 경찰청 http, //www, police |  |
| 213 | draft-cegghacigobabaec | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 팩스, 김태진, 김태진 팩스, 주식회사, 플라시스템 | 주소, 부산광역시, 주소 부산광역시, 남구, 남동천로 |  |
| 214 | draft-amagmcfbechldabf | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 전화, -, - 전화, 담당자, 장중원 | /, 이메일, / 이메일, ac, kr |  |
| 215 | draft-blgicoabeaojipnj | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | kr, co, co kr, http, //www | 하단메뉴, --, 하단메뉴 --, 패밀리, 사이트 |  |
| 216 | draft-bdmhpjmfjeplahgb | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 공정상생센터, 콘텐츠분쟁조정위원회, 콘텐츠분쟁조정위원회 공정상생센터, 정보보안팀, 대중문화예술종합정보시스템 | 게임국가기술자격검정, 게임기반조성팀, 게임국가기술자격검정 게임기반조성팀, ​모바일/VR게임테스트베드, 이행 |  |
| 217 | draft-aeondgkifoipcebj | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 건강검진예약, 1599-3114, 1599-3114 건강검진예약, 예약확인, 진료예약 | 약처방문의, 약처방전재발급, 약처방문의 약처방전재발급, 입원비확인ARS, 응급실 |  |
| 218 | draft-anafgmgfgefbnkdc | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | kr, 연락처, 연락처 kr, 부서, 부서명 | ※, 정보주체께서는, ※ 정보주체께서는, 열람청구, 접수·처리부서 |  |
| 219 | draft-hpoepbikmkpeijgi | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | customer_support | public_web_context | non_pii | 사업자등록번호, 김용선, 김용선 사업자등록번호, 주식회사, 카멜인터내셔널 | 본사, 서울특별시, 본사 서울특별시, 금천구, 디지털로 |  |
| 220 | draft-djcljjcpmamjddad | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 등록번호, 사업자, 사업자 등록번호, 통신판매업신고번호, 제 | 주식회사, 플라시스템, 주식회사 플라시스템, All, Right |  |
| 221 | draft-ejboppnmgfpkcpoj | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | education | public_web_context | non_pii | 사업자등록번호 |  |  |
| 222 | draft-lbaijgfbhnfcknhf | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | enterprise_internal | public_web_context | non_pii | 확인하고, 부분을, 부분을 확인하고, 사업자등록번호, 잘못 | 으로, 변경했을, 으로 변경했을, 경우, 이전 |  |
| 223 | draft-gkemdjicppeohaeh | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | general_web | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, 대표이사, 김기원 | /, 전화주문, / 전화주문, 1600-5252, COPYRIGHT |  |
| 224 | draft-fojnccacfefhnimb | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, 대표전화, 1599-3114 | 박승우, copyright©1996-2015, 박승우 copyright©1996-2015, by, Samsung |  |
| 225 | draft-cnmlbifkpgclalbg | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 행사, 나눔, 나눔 행사, 2026-03-08, 외국인근로자 | 센터행사, 자세히보기, 센터행사 자세히보기, 상담사례, 오시는길 |  |
| 226 | draft-ipojbibkhnphklnb | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 상담, 처리 상담 |  |
| 227 | draft-ajkofceankenflfn | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 시행일, 215차, 215차 시행일, 2025-02-12, 개인정보처리방침 | 개인정보처리방침, 214차, 개인정보처리방침 214차, 시행일, 2024-11-12 |  |
| 228 | draft-bkhpphdamdmlpodn | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 선택, 생년월일, 생년월일 선택, 지원자, 성명 | 2009, 2008, 2009 2008, 2007, 2006 |  |
| 229 | draft-biipfcjmkhlgfddp | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 230 | draft-fkdmeigjdmfmckkl | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 선택, 첫째자리, 첫째자리 선택, 필수입력, 휴대전화 | 019, -, 019 -, 휴대전화, 중간자리 |  |
| 231 | draft-fagkikjlclaiemog | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 입금, 환불 입금 | 처리, 심사, 처리 심사 |  |
| 232 | draft-eibdfokmengflacp | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 114, 269, 269 114, 595, 769 | 636, 122, 636 122, 632, 582 |  |
| 233 | draft-fllkhhfeefdgkdbl | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | ISMS-KISA-, ISMS, ISMS ISMS-KISA-, 번호, 유효기간 | 11, 04, 11 04, ~, 2026 |  |
| 234 | draft-hdfjbgejfaidnojc | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 예약, 처리 예약 |  |
| 235 | draft-ekmbadokgakgnpkf | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2025-12-12 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 236 | draft-kngechogcnpaicej | BANK_ACCOUNT | BANK_ACCOUNT | public_services | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 발급, 입금 | 처리, 민원, 처리 민원 |  |
| 237 | draft-ienoilnepgobahje | EMAIL | EMAIL | customer_support | public_web_context | non_pii | 이메일, 또는, 또는 이메일, 행사방법, 이용자는 | 을, 통해, 을 통해, 개인정보, 열람 |  |
| 238 | draft-hfpoficmhllpmkhm | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 상담, 상담 인증 | 발송, 접수, 발송 접수 |  |
| 239 | draft-aihnghhgeoghoddc | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 전화번호, 전화번호 이메일, 고객서비스담당, 부서 | o, 개인정보, o 개인정보, 보호담당자, 성명 |  |
| 240 | draft-dpjlnafjmchjppgi | EMAIL | EMAIL | education | public_web_context | non_pii | 1301, 국번없이, 국번없이 1301, kr, 대검찰청 | http, //spo, http //spo, go, kr |  |
| 241 | draft-kaghkmhpkhkdhcne | EMAIL | EMAIL | education | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 등록, 등록 인증 | 발송, 신청, 발송 신청 |  |
| 242 | draft-dmebaidgbakmanlg | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 243 | draft-ddhhaknadkfbblpg | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 244 | draft-dbpaeppgflhofgln | EMAIL | EMAIL | general_web | public_web_context | non_pii | 메일, -, - 메일, 이찬응, 전화번호 | 12 |  |
| 245 | draft-cagglbbdaiemplim | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 책임자, 책임자 이메일, 전화번호, 02 | 장례서비스, 개인정보, 장례서비스 개인정보, 관리, 부서 |  |
| 246 | draft-dodfapjmgpliidij | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, ·, · 이메일, 전화, 팩스 | ②, 정보주체는, ② 정보주체는, 제1항의, 열람청구 |  |
| 247 | draft-llijboonocdbgolh | PHONE | PHONE_LANDLINE | customer_support | public_web_context | non_pii | 전화, kr, kr 전화, //www, privacymark | 대검찰청, 인터넷범죄수사센터, 대검찰청 인터넷범죄수사센터, http, //www |  |
| 248 | draft-cemilbfcjabgbeao | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 전화번호, 사업본부, 사업본부 전화번호, 소속, 온라인 | 이메일, co, 이메일 co, kr, o |  |
| 249 | draft-aplgjpimgkdecbib | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | ㈜아이오시스, 관리, 관리 ㈜아이오시스, IWCC클라우드, 서비스 | 2026 |  |
| 250 | draft-bndjkpakoomiddjk | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 당직실, 팩스번호, 팩스번호 당직실, 하광교동, 민원실 | 1918, 찾아오시는, 1918 찾아오시는, 길, 인스타그램 |  |
| 251 | draft-bhpbailbikdbmhbc | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 과장, 김학균, 김학균 과장, 기업부설창작연구소, 한국문화기술기획평가원 | 콘텐츠수출마케팅플랫폼, 수출전략팀, 콘텐츠수출마케팅플랫폼 수출전략팀, 이윤주, 주임 |  |
| 252 | draft-ahihpheefkknoboh | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 문의, 00, 00 문의, ~, 16 | 편의시설, 안내, 편의시설 안내, 관련, 상세 |  |
| 253 | draft-animiindhkijgagm | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 전화, -, - 전화, 재난안전교육포탈, 회원정보 | -, 팩스, - 팩스, 이메일, kr |  |
| 254 | draft-ifngfkkhfapojlch | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | customer_support | public_web_context | non_pii | 사업자등록번호, 제2015-경기파주7090호, 제2015-경기파주7090호 사업자등록번호, co, kr | 사업자번호조회, 최근, 사업자번호조회 최근, 본, 상품 |  |
| 255 | draft-egkkkkkagmnmflnk | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 정동훈, 정동훈 사업자등록번호, 애니메이트, 홍대점 | 사업자정보확인, 통신판매업신고번호, 사업자정보확인 통신판매업신고번호, 2020-서울마포-2540, 전화 |  |
| 256 | draft-haeejplgjgcfppgc | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | education | public_web_context | non_pii | 고유번호, 제2014-서울강북-0056, 제2014-서울강북-0056 고유번호, 솔매로49길, 60 | 총장, 이은주, 총장 이은주, 대표전화, FAX |  |
| 257 | draft-mnbakjmfnoffngbi | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | enterprise_internal | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, 대표이사, 이호웅 | 고객센터, 1899-9100, 고객센터 1899-9100, 지역선택, 1번 |  |
| 258 | draft-hiijjedkocdagamk | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | general_web | public_web_context | non_pii | 고유번호, 제2013-서울광진-0147호, 제2013-서울광진-0147호 고유번호, ac, kr | 2023, Sejong, 2023 Sejong, Cyber, University |  |
| 259 | draft-gdiclahobcecddcn | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 사업자번호, 강윤식, 강윤식 사업자번호, 더보기, -- | 서울시, 서초구, 서울시 서초구, 서초중앙로, 4 |  |
| 260 | draft-cnplnoblmbljcpec | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 12~2월28, 1, 1 12~2월28, 한글교육생, 모집 | 유용한, 정보, 유용한 정보, E-7-4, 체류자경 |  |
| 261 | draft-kckgpepleelmndec | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 상담, 상담 환불 | 확인, 접수, 확인 접수 |  |
| 262 | draft-ajooniidbmdihkfd | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 업데이트, 최종, 최종 업데이트 | •, 사업자, • 사업자, ㈜플라시스템, 서비스 |  |
| 263 | draft-bocpehlofemiehbg | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 휴대전화, *, * 휴대전화, 이름, * 이름 | 019, *, 019 *, 이메일, 직접입력하기 |  |
| 264 | draft-cgadpleeoabbagih | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 265 | draft-fobjodhklncmffbp | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | BENEDR-, 44444444, 44444444 BENEDR-, 11111111, 21222222 | 추가, --, 추가 --, -- --, 추가 -- -- |  |
| 266 | draft-feeihbjjgjbkbpcp | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 입금, 환불 입금 | 처리, 심사, 처리 심사 |  |
| 267 | draft-fhdjpbiejkphcjmg | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 고객센터 | 개인정보관리책임자, 김철홍, 개인정보관리책임자 김철홍, 이메일, mcd |  |
| 268 | draft-gbaokfajkjemeaai | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | +, English, English +, 국제성모병원, 대표번호 | Russian, 응급의료센터, Russian 응급의료센터, 야간, 1600-6119 |  |
| 269 | draft-lgekhaofhnmnklmc | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 예약, 처리 예약 |  |
| 270 | draft-eldidmifghbdbhhg | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2025-05-13 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 271 | draft-lljkafficgcmbhbh | BANK_ACCOUNT | BANK_ACCOUNT | public_services | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 발급, 입금 | 처리, 민원, 처리 민원 |  |
| 272 | draft-jefdbiiddmobaphl | EMAIL | EMAIL | customer_support | public_web_context | non_pii | 휴무, 공휴일, 공휴일 휴무, 00, 주말 | 사업자정보확인, 서비스소개, 사업자정보확인 서비스소개, 원격지원, 서비스 |  |
| 273 | draft-hgcpmeeblmpebepg | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 상담, 상담 인증 | 발송, 접수, 발송 접수 |  |
| 274 | draft-aimghlclfakmlipf | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, -, - 이메일, 고객지원센터, 전화 | 회사는, 쿠키, 회사는 쿠키, 및, 타사가 |  |
| 275 | draft-gjppfjbnjhgepccm | EMAIL | EMAIL | education | public_web_context | non_pii | 예, 이메일, 이메일 예, 성별, 남 | 지원자, 연락처, 지원자 연락처, 선택, 010 |  |
| 276 | draft-kljjehekmlandfpd | EMAIL | EMAIL | education | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 등록, 등록 인증 | 발송, 신청, 발송 신청 |  |
| 277 | draft-fgcpjbjnehjlknbc | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 278 | draft-dfblbkebgkapjhfp | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 환불, 안내 | 확인, 심사, 확인 심사 |  |
| 279 | draft-eecbgadflgjbphpo | EMAIL | EMAIL | general_web | public_web_context | non_pii | 이메일, 6316, 6316 이메일, -, 연락처 | 콘텐츠, 만족도, 콘텐츠 만족도, 조사, 이 |  |
| 280 | draft-cboonegkaoeldfod | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 책임자, 책임자 이메일, 전화번호, 02 | 새생명후원회, 의료사회복지서비스, 새생명후원회 의료사회복지서비스, 개인정보, 관리 |  |
| 281 | draft-ecicjhpaolcgppcg | EMAIL | EMAIL | public_services | public_web_context | non_pii | 연락처, 신승희, 신승희 연락처, 개인정보보호, 담당자 | 정보주체께서는, 국가민방위재난안전교육원의, 정보주체께서는 국가민방위재난안전교육원의, 서비스를, 이용하시면서 |  |
| 282 | draft-njobldkahcekeajh | PHONE | PHONE_LANDLINE | customer_support | public_web_context | non_pii | FAX, TEL, TEL FAX, 문발로, 112 | 대표이사, 이종춘, 대표이사 이종춘, 개인정보관리자, 노수현 |  |
| 283 | draft-cjdakedneimkfpio | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | FAX, /, / FAX, 제, 2016-0099505 | 이메일, com, 이메일 com, 1, 1문의 |  |
| 284 | draft-bcoeoimgaombcfff | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 접수문의사항, 돌아가기, 돌아가기 접수문의사항, 수험번호, 수험번호 돌아가기 |  |  |
| 285 | draft-cdkhppmanddonjlm | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | FAX, /, / FAX, 42-15, TEL | /, E-mail, / E-mail, com, 46004 |  |
| 286 | draft-bidipiocleoobhnc | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 전화번호, -, - 전화번호, 담당자, DT지원팀 | -, 메일, - 메일, com, 12 |  |
| 287 | draft-ajjelmpippkolohp | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 진료예약, --, -- 진료예약, 창, 바로가기 | 8300, 서울적십자병원, 8300 서울적십자병원, 병원소개, 서울적십자병원 병원소개 |  |
| 288 | draft-aplaopiblegblfon | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 연락처, 신승희, 신승희 연락처, 개인정보보호, 담당자 | kr, 정보주체께서는, kr 정보주체께서는, 국가민방위재난안전교육원의, 서비스를 |  |
| 289 | draft-jljjgdmniicphnkc | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | customer_support | public_web_context | non_pii | No, registration, registration No, SungHwan, Kim | E-commerce, Registration, E-commerce Registration, No, Registration No |  |
| 290 | draft-fmeaakhphiffjnmi | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 김도균, 김도균 사업자등록번호, 주식회사, 에이비티아시아 | 사업자, 등록번호, 사업자 등록번호, 조회, 주소 |  |
| 291 | draft-halmgchfpoagdcaa | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | education | public_web_context | non_pii | 사업자등록번호, 장지호, 장지호 사업자등록번호, Tel, Fax | 통신판매업신고번호, 제2014-서울동대문-0532호, 통신판매업신고번호 제2014-서울동대문-0532호, Copyright, C |  |
| 292 | draft-iebajekhigbdkgad | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | general_web | public_web_context | non_pii | n, 00000, 00000 n, f, f 00000 | 00000, n, 00000 n, n 00000, 00000 n 00000 |  |
| 293 | draft-gmkmiakbgejhnbjb | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, 대표자, 이동진 | COPYRIGHT, ⓒ, COPYRIGHT ⓒ, 2023, HALLYM |  |
| 294 | draft-dfikekfebbnibcbf | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 고객센터, 4, 4 고객센터, 1, 2 | 상담, 10, 상담 10, 00, ~ |  |
| 295 | draft-lbpkmnkllgbkaekm | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 상담, 상담 환불 | 확인, 접수, 확인 접수 |  |
| 296 | draft-akdbebkkilloklbo | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 업데이트, 최종, 최종 업데이트 | •, 서비스, • 서비스, 꽃파는총각, 운영 |  |
| 297 | draft-ccajgckhpgpjjjhf | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 환불기준, 수강료, 수강료 환불기준, 시험, 메뉴얼 | 수강료, 반환, 수강료 반환, 및, 환불 |  |
| 298 | draft-cmkmpcnoejnahphe | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 299 | draft-ggeigigoombbgpei | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | +, 때, 때 +, 해외에서, 국내로 | 기업전용, 1599-9499, 기업전용 1599-9499, 기업, B2B |  |
| 300 | draft-hcccgjmpfmiopkjj | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 301 | draft-jcddigjmeikgjbkp | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 고객센터 | 개인정보보호책임자, 김철홍, 개인정보보호책임자 김철홍, 이메일, mcd |  |
| 302 | draft-gbgjgnbnjehjpimj | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 선택, 00, 00 선택, 10, ~ | 019, -, 019 -, 신청, 휴대폰 |  |
| 303 | draft-mmimgcpcepekbjpg | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 예약, 예약 환불 | 확인, 접수, 확인 접수 |  |
| 304 | draft-fadlophidecgmbeg | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2026-02-11 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 305 | draft-nnlpokmakhcdalbn | BANK_ACCOUNT | BANK_ACCOUNT | public_services | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 발급, 입금 | 처리, 민원, 처리 민원 |  |
| 306 | draft-jppobkdpdgpjjgdi | EMAIL | EMAIL | customer_support | public_web_context | non_pii | 휴무, 주말/공휴일, 주말/공휴일 휴무, 10~17시, 12~13시반 | ★, 즐겨찾기, ★ 즐겨찾기, 로그인, 회원가입 |  |
| 307 | draft-hohlobcfajnnboli | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 상담, 상담 인증 | 발송, 접수, 발송 접수 |  |
| 308 | draft-baojhnbdonnonnen | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 시까지, 요청, 요청 시까지, 종료, 또는 | ※, 국외이전, ※ 국외이전, 거부, 방법·절차 |  |
| 309 | draft-hieacffcmlckcffd | EMAIL | EMAIL | education | public_web_context | non_pii | 문의, 사전, 사전 문의, 또는, 전화 | +82-2-944-5000, Contact, +82-2-944-5000 Contact, 연락처, 입학 |  |
| 310 | draft-koajocofhjlkjeim | EMAIL | EMAIL | education | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 등록, 등록 인증 | 발송, 신청, 발송 신청 |  |
| 311 | draft-gcoclicdgjfjapfp | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 요청, 요청 인증 | 발송, 승인, 발송 승인 |  |
| 312 | draft-gcdgbekkmokccnjp | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 환불, 안내 | 확인, 심사, 확인 심사 |  |
| 313 | draft-fkfjlaecmigbgdkb | EMAIL | EMAIL | general_web | public_web_context | non_pii | 학생지원팀장, 학생지원처장, 학생지원처장 학생지원팀장, 입시, 홍보 | 02, 2204-8007, 장학, 졸업생관리, 상담 |  |
| 314 | draft-dfjdkgcjjeaekfdk | EMAIL | EMAIL | healthcare | public_web_context | non_pii | com | Copyright, c, Copyright c, Kyungpook, National |  |
| 315 | draft-faniljafgogionno | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, ·, · 이메일, 전화, 팩스 | 법무감사담, 당관실, 법무감사담 당관실, -, 포털 |  |
| 316 | draft-onbgkppboanaanmm | PHONE | PHONE_LANDLINE | customer_support | public_web_context | non_pii | 팩스, ㅣ, ㅣ 팩스, 2014-서울중랑-0456호, 전화 | 주소, 서울시, 주소 서울시, 중랑구, 신내역로111 |  |
| 317 | draft-dljehhlfagfpggph | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 팩스번호, -, - 팩스번호, 전화번호, 국번없이 | -, 주, - 주, 소, 13992 |  |
| 318 | draft-bdokpmfjcgninbhk | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | ㈜아르고넷, 대행, 대행 ㈜아르고넷, 중앙도서관, OAK시스템 | 2026 |  |
| 319 | draft-cepmfocjcddnfbjk | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 전화번호, 민원실, 민원실 전화번호, 광교산로, 119 | 팩스번호, 당직실, 팩스번호 당직실, 1918, 찾아오시는 |  |
| 320 | draft-bpegcacbcodlfbgh | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 없음 | 이행, 게임더하기, 이행 게임더하기, 게임유통팀, 홈페이지 |  |
| 321 | draft-algoamikekfkejpe | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 진료상담, 진료의뢰, 진료의뢰 진료상담, 회송환자, 로그인 | 로그인없는, 진료의뢰, 로그인없는 진료의뢰, 로그인, 없는 |  |
| 322 | draft-bgaafecmjlkpecdf | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 가름로, 143 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 323 | draft-mggibpondpdcedem | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | customer_support | public_web_context | non_pii | 사업자번호, 노인석, 노인석 사업자번호, 주식회사, 우수패밀리 | 주소, 경기도, 주소 경기도, 고양시, 일산서구 |  |
| 324 | draft-hijkepnmoadbfmbd | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 3가, 3가 사업자등록번호, 6층, 1-1호 | 통신판매업, 신고, 통신판매업 신고, 제2007-서울용산-04838, 개인정보보호책임자 |  |
| 325 | draft-hhocmlmmkdlfadfn | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | education | public_web_context | non_pii | 사업자등록번호, FAX, FAX 사업자등록번호, 원광디지털대학교, TEL | 대표, 김윤철, 대표 김윤철, Copyright, C |  |
| 326 | draft-okedgedcbioiffhp | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | general_web | public_web_context | non_pii | 23, 0, 0 23, obj, endobj | 65535, f, 65535 f, 00000, n |  |
| 327 | draft-hgklkkobembbgiff | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, 대표전화, 1599-3114 | 박승우, copyright©1996-2015, 박승우 copyright©1996-2015, by, Samsung |  |
| 328 | draft-dkkmldnffefbjngb | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 안내, 참여, 참여 안내, 2026-04-24, 광역형비자 | f-3비자에, 대해서, f-3비자에 대해서, 2026-02-06, G1 |  |
| 329 | draft-mcopppcffjikcbnc | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 상담, 상담 환불 | 확인, 접수, 확인 접수 |  |
| 330 | draft-amogomnlccfkiaap | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 169차, 169차 변경일, 2020-12-21, 개인정보처리방침 | 개인정보처리방침, 168차, 개인정보처리방침 168차, 변경일, 2020-11-28 |  |
| 331 | draft-chdflakfdbhkiinf | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 9, 8, 8 9, 5, 6 | 월, 선택, 월 선택, 1, 2 |  |
| 332 | draft-digcelngoimcbleb | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 333 | draft-igegniankhilpjaf | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 자동이체통합관리, --, -- 자동이체통합관리, 골든라이프뱅킹, KB드림톡적금 | --, 보안센터, -- 보안센터, 인증센터, 개인 |  |
| 334 | draft-hdnanohiacgoidgm | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 335 | draft-jclcanfojbnlppph | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 136, 500, 500 136, 130, 132 | 341, 605, 341 605, 571, 241 |  |
| 336 | draft-ginnlbdcggogcmhd | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 자, 제공받는, 제공받는 자, 처리, 기간 | 수술, 후, 수술 후, 통증감소를, 위해 |  |
| 337 | draft-nadipikabialeplm | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 예약, 처리 예약 |  |
| 338 | draft-fblajflmindnnhgo | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2025-12-09 |  |
| 339 | draft-kcnobkbjmbfllcdi | EMAIL | EMAIL | customer_support | public_web_context | non_pii | 노수현, 개인정보관리자, 개인정보관리자 노수현, FAX, 대표이사 | 통신판매업신고번호, 제2015-경기파주7090호, 통신판매업신고번호 제2015-경기파주7090호, 사업자등록번호, 사업자번호조회 |  |
| 340 | draft-ijkjiljomdckigkm | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 상담, 상담 인증 | 발송, 접수, 발송 접수 |  |
| 341 | draft-bdggkpnjcpijoojp | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 1544-3800, 고객만족센터, 고객만족센터 1544-3800, 본문, 확인 | 제1조, 개인정보의, 제1조 개인정보의, 처리, 목적 |  |
| 342 | draft-hoipfmjkceoambei | EMAIL | EMAIL | education | public_web_context | non_pii | e-mail, 전성희, 전성희 e-mail, /, 사업자등록번호 | 신입생, 입학상담, 신입생 입학상담, tel, / |  |
| 343 | draft-hcgicgedpdfegbgo | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 344 | draft-hgjfnpehjkcfgmeo | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 345 | draft-fokijoahonpeieoj | EMAIL | EMAIL | general_web | public_web_context | non_pii | 이메일, 또는, 또는 이메일, 서식을, 통해 | 로, 이의를, 로 이의를, 제기할, 수 |  |
| 346 | draft-djlakkokbaaempgi | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 1688-7575, TEL, TEL 1688-7575, 43길, 88 | by, Asan, by Asan, Medical, Center |  |
| 347 | draft-fcngpahnfjneidnd | EMAIL | EMAIL | public_services | public_web_context | non_pii | 연락처, 권구열, 권구열 연락처, 개인정보보호, 담당자 | 정보주체께서는, 국가민방위재난안전교육원의, 정보주체께서는 국가민방위재난안전교육원의, 서비스를, 이용하시면서 |  |
| 348 | draft-pdhbaidclichnmfo | PHONE | PHONE_LANDLINE | customer_support | public_web_context | non_pii | Fax, 1811-4493, 1811-4493 Fax, 가산동, 아이에스비즈타워 | E-mail, co, E-mail co, kr, 통신판매업신고 |  |
| 349 | draft-dojjogliekobbkdl | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 팩스, 김태진, 김태진 팩스, 주식회사, 플라시스템 | 주소, 부산광역시, 주소 부산광역시, 남구, 남동천로 |  |
| 350 | draft-bgbjibnfenkemcgp | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 신기술교육원, 입학문의, 입학문의 신기술교육원, MENU, 학생정보시스템 | 전국, 과정문의, 전국 과정문의, 1588-2282, 예비신입생 |  |
| 351 | draft-choplkbhdncnpeco | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 말씀, 고객의, 고객의 말씀, 해외, +82 | 신규상담, 예적금, 신규상담 예적금, 1599-8100, 대출 |  |
| 352 | draft-cbephkddgeimcbkf | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 대중음악산업팀, 대중문화예술종합정보시스템, 대중문화예술종합정보시스템 대중음악산업팀, 전사적자원, 관리시스템 | 콘텐츠분쟁조정위원회, 공정상생센터, 콘텐츠분쟁조정위원회 공정상생센터, 게임국가기술, 자격검정 |  |
| 353 | draft-alplhngopflfnlli | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 진료의뢰·협력, 장례식장, 장례식장 진료의뢰·협력, 입원비확인ARS, 응급실 | --, 홈페이지/앱이용문의, -- 홈페이지/앱이용문의, 오시는, 길 |  |
| 354 | draft-binpfljfmddmhigd | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 김직동, 권리, 권리 김직동, 김면기, 개인정보보호정책과장 | 데이터안전정책과장, 가명정보, 데이터안전정책과장 가명정보, 태현수, 자율보호정책과장 |  |
| 355 | draft-ihbckgfneimhiiek | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, com, com 사업자등록번호, 세교산단로, 67-20 | 통신판매신고번호, 2018-경기평택-0099, 통신판매신고번호 2018-경기평택-0099, 부가통신사업신고필증, - |  |
| 356 | draft-jmhgihmofdmckeal | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | education | public_web_context | non_pii | 고유번호, 제2014-서울강북-0056, 제2014-서울강북-0056 고유번호, 솔매로49길, 60 | 총장, 이은주, 총장 이은주, 대표전화, FAX |  |
| 357 | draft-papedocglfkkmdnl | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | general_web | public_web_context | non_pii | n, 00000, 00000 n, n 00000, n 00000 n | 00000, n, 00000 n, n 00000, 00000 n 00000 |  |
| 358 | draft-hioepnhkgdloegei | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, 박종현, TEL | ©2020, NOW, ©2020 NOW, HOSPITAL, All |  |
| 359 | draft-eohcindagcedocdi | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 연락처, •, • 연락처, 개인정보보호책임자, 성영주 | /, co, / co, kr, • |  |
| 360 | draft-nfbbnpmpknpkjcok | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 상담, 처리 상담 |  |
| 361 | draft-apmbiinijalcadhn | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 158차, 158차 변경일, 2020-04-01, 개인정보처리방침 | 개인정보처리방침, 157차, 개인정보처리방침 157차, 변경일, 2019-12-19 |  |
| 362 | draft-dcmhmddjngalcogh | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 신청서, 환불, 환불 신청서, 수강료, 반환 | 교내캠퍼스안내, 개인정보처리방침, 교내캠퍼스안내 개인정보처리방침, 이메일무단수집거부, 이메일 |  |
| 363 | draft-doahnjfjpaegloec | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 364 | draft-jhcgmgmfmgipeejd | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 054, 053, 053 054, 043, 051 | 070, 080, 070 080, -, 연락처 |  |
| 365 | draft-imndjeoeghpjncfi | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 366 | draft-jicnogaaabkakgpd | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 574, 574 574 | 101, 625, 101 625, 104, 645 |  |
| 367 | draft-gldcpnjoaejlicin | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 선택, 00, 00 선택, 10, ~ | 019, -, 019 -, 신청, 휴대폰 |  |
| 368 | draft-pggomkbmaoboampe | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 예약, 예약 환불 | 확인, 접수, 확인 접수 |  |
| 369 | draft-fflhihibclpdpkcf | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2025-07-31 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 370 | draft-kjijpjeanabmajba | EMAIL | EMAIL | customer_support | public_web_context | non_pii | 이메일, FAX, FAX 이메일, 통신판매업신고, 제 | Copyright, ©, Copyright ©, 2020, 플레이통 |  |
| 371 | draft-kkmajncelloahokl | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 상담, 상담 인증 | 발송, 접수, 발송 접수 |  |
| 372 | draft-bfhfjkipdiokkpfm | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | Datadog, 기간까지, 기간까지 Datadog, 있는, 경우는 | 미국, 달다방, 미국 달다방, 서비스, 이용 |  |
| 373 | draft-jdhdmemaobelonmb | EMAIL | EMAIL | education | public_web_context | non_pii | 안효석, 사무처장, 사무처장 안효석, 스, 이메일 | 개인정보보호담당자, 개인정보보호담당자에, 개인정보보호담당자 개인정보보호담당자에, 대한, 소속 |  |
| 374 | draft-hdhcfnbenfjheobo | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 375 | draft-japalgknaiicfpin | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 376 | draft-hdmmmeodfeodfcip | EMAIL | EMAIL | general_web | public_web_context | non_pii | 담당부서, 개인정보보호, 개인정보보호 담당부서, 및, 설명 | 에, 요청할, 에 요청할, 수, 있습니다 |  |
| 377 | draft-ephjfflgkegiffef | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 전산정보팀장, 부서, 부서 전산정보팀장, 보유, 개인정보 | 제1조, 개인정보의, 제1조 개인정보의, 처리목적, 제2조 |  |
| 378 | draft-fegkeifmkkdpmbai | EMAIL | EMAIL | public_services | public_web_context | non_pii | 연락처, 기획협력과, 기획협력과 연락처, 접수・처리, 부서 | ※, 정보주체께서는, ※ 정보주체께서는, 열람청구, 접수·처리부서 |  |
| 379 | draft-eepiblplhoolhaib | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | FAX, 022094, 022094 FAX, 2018-경기평택-0099, 부가통신사업신고필증 | 개인정보관리책임자, 김태은, 개인정보관리책임자 김태은, 우인환, 1 |  |
| 380 | draft-bhkdfbbigncljbnd | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | fax, /, / fax, 신입생, 입학상담 | 재학생, 교학처, 재학생 교학처, tel, COPYRIGHT |  |
| 381 | draft-conabgbidhebghko | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 대표번호, 풍세로708, 풍세로708 대표번호, 충청남도, 천안시 | 홈페이지, https, 홈페이지 https, //nanum, ff |  |
| 382 | draft-cbfbnnbbnobcappd | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 과장, 김인정, 김인정 과장, 개인정보, 보호담당자 | 개인정보, 보호담당자, 개인정보 보호담당자, 정보보안팀, 김자연 |  |
| 383 | draft-bbljmnjaocdkkbhl | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 연락처, 원무팀, 원무팀 연락처, 진료예약, 바로가기 | 오류신고하기, --, 오류신고하기 --, PNUH, 네트워크 |  |
| 384 | draft-bmjeiiimdaacaiji | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 박상연, 기획협력과, 기획협력과 박상연, 전화, 전자우편 | kr, -, kr -, ②, 정보주체께서는 |  |
| 385 | draft-iibbfdinmhekcpna | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 이랜드글로벌R&D센터, 이랜드글로벌R&D센터 사업자등록번호, 마곡동로, 146 | 통신판매업신고번호, 제2025-서울강서-2260, 통신판매업신고번호 제2025-서울강서-2260, 개인정보보호책임자, 민혜정 |  |
| 386 | draft-kdifhcgajhfmaofa | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | education | public_web_context | non_pii | 사업자등록번호, Fax, Fax 사업자등록번호, Tel, 0212 | Copyright, DAEDUK, Copyright DAEDUK, UNIVERSITY, All |  |
| 387 | draft-pogphedbmgbpdinp | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | general_web | public_web_context | non_pii | n, 00000, 00000 n, n 00000, n 00000 n | 00000, n, 00000 n, trailer, %iText-5 |  |
| 388 | draft-hphjdijghgdohaea | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 등록번호, 사업자, 사업자 등록번호, 법인명, 서울특별시 | 대표자, 이현석, 대표자 이현석, copyright, by |  |
| 389 | draft-fnbgnfhjamghmmga | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 필리핀농구대회, 포토갤러리, 포토갤러리 필리핀농구대회, 2026-01-17, Photo | 필리핀, 자매들의, 필리핀 자매들의, 구미보, 나들이 |  |
| 390 | draft-nlglkjabbldkcblh | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 상담, 상담 환불 | 확인, 접수, 확인 접수 |  |
| 391 | draft-bahjboimnlcjkome | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 고객센터, 박준태, 박준태 고객센터, 통신판매업신고번호, 2025-경기김포-7398 | 창업문의, 1544-6266, 창업문의 1544-6266, Copyright, 2021 |  |
| 392 | draft-dgkacngfcjbefigb | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 선택, 부, 부 선택, 보호자, 연락처 | 019, 070, 019 070, -, 보호자 |  |
| 393 | draft-eekaopefglgpcmaf | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 394 | draft-joabelimmoniieca | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 휴대전화, 070, 070 휴대전화, 062, 063 | 4, 지원대상, 4 지원대상, 참여신청, 근로자 |  |
| 395 | draft-jdbkmpkmgmilbjdk | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 입금, 환불 입금 | 처리, 심사, 처리 심사 |  |
| 396 | draft-kgcobdaldkmfmjpf | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 567, 605, 605 567, 562, 572 | 500, 231, 500 231, 861, 580 |  |
| 397 | draft-iblbjlaaebbadbmg | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | *, 전화번호, 전화번호 *, 일, - | 019, 070, 019 070, 02, 서울 |  |
| 398 | draft-fjnfkkmijlmjlbjg | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2026-02-11 |  |
| 399 | draft-mcplagdhijniegic | EMAIL | EMAIL | customer_support | public_web_context | non_pii | 이메일, /, / 이메일, 전화, 1666-3009 | 회사명, 담당자, 회사명 담당자, 이메일, 연락처 |  |
| 400 | draft-ldgkiplidofbmgeh | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 상담, 상담 인증 | 발송, 접수, 발송 접수 |  |
| 401 | draft-bgfgaalhkobflicn | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | Paypal, 연락처, 연락처 Paypal, 이전받는, 자 | 개인정보가, 이전되는, 개인정보가 이전되는, 국가, 미국 |  |
| 402 | draft-jpbpcnldgojclogp | EMAIL | EMAIL | education | public_web_context | non_pii | 곽은영, 당, 당 곽은영, 이메일, 인사총무팀 | 개인정보보호, 분임책임자, 개인정보보호 분임책임자, 청주대학교는, 개인정보의 |  |
| 403 | draft-hpnnbaalckoiehnb | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 404 | draft-jmfgdmeefdcifphe | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 405 | draft-iiibplkeoallimmf | EMAIL | EMAIL | general_web | public_web_context | non_pii |  | -, 콘진원, - 콘진원, 담당자를, 통한 |  |
| 406 | draft-fmhakjpolpbnkaim | EMAIL | EMAIL | healthcare | public_web_context | non_pii | e-mail, 7000, 7000 e-mail, 02, 2276 | 법인명, 서울특별시, 법인명 서울특별시, 서울의료원, 사업자 |  |
| 407 | draft-fgdcenhbmigbpgci | EMAIL | EMAIL | public_services | public_web_context | non_pii | 연락처, 강병연, 강병연 연락처, 개인정보보호, 담당자 | 정보주체께서는, 국가민방위재난안전교육원의, 정보주체께서는 국가민방위재난안전교육원의, 서비스를, 이용하시면서 |  |
| 408 | draft-ehlgfkhmoofhbgkm | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 전화번호, 지피클럽, 지피클럽 전화번호, 성명, 안병근 | 이메일, gpmd, 이메일 gpmd, co, kr |  |
| 409 | draft-bjkednnafifcjadd | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 총무팀, 부서, 부서 총무팀, 업무를, 담당하고 | 에, 다음, 에 다음, 서식에, 따라 |  |
| 410 | draft-egbghlcfdinkifpn | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | com, next-securities, next-securities com, X, http | 리딩투자증권, ○, 리딩투자증권 ○, X, http |  |
| 411 | draft-cgfgdlemmcgdfimm | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | /, kr, kr /, www, eprivacy | ~4, 인터넷범죄수사센터, ~4 인터넷범죄수사센터, http, //spo |  |
| 412 | draft-bhdbaolcfndehieg | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 연락처, 의무기록팀, 의무기록팀 연락처, 중앙암등록본부, 고충처리부서 | ※, 세부, ※ 세부, 항목은, 개인정보 |  |
| 413 | draft-bomaipfpkpojcico | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 재난안전교육과, 교육문의, 교육문의 재난안전교육과, 09, 00-18 | 민방위비상대비교육과, COPYRIGHT, 민방위비상대비교육과 COPYRIGHT, C, National |  |
| 414 | draft-iigiiaeffcilijoe | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 등록번호, 사업자, 사업자 등록번호, 140-1, 텐모어플러스 | /, 통신판매업신고번호, / 통신판매업신고번호, 제, 2023-진접오남-0081호 |  |
| 415 | draft-ocfnjpjgffkfccfe | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | education | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, 37, 대표 | 관리자, 전성희, 관리자 전성희, e-mail, com |  |
| 416 | draft-jniihccaacnlhmlb | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 등록번호, 사업자, 사업자 등록번호, 법인명, 서울특별시 | 대표자, 이현석, 대표자 이현석, copyright, by |  |
| 417 | draft-fphmjjpmjplkaamb | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 돕기, 이해, 이해 돕기, G1, 비자에 | 비자에, 대한, 비자에 대한, 이해, 돕기 |  |
| 418 | draft-npobbhfenbiepikd | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 상담, 처리 상담 |  |
| 419 | draft-bahkjmfhdnmgbead | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 187차, 187차 변경일, 2022-07-29, 개인정보처리방침 | 개인정보처리방침, 186차, 개인정보처리방침 186차, 변경일, 2022-05-20 |  |
| 420 | draft-dmfghgkmejgmfjii | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 년도, 필수, 필수 년도, *주민번호, 뒤 | *모집시기, 필수, *모집시기 필수, 수시1차, 수시2차 |  |
| 421 | draft-eemgkjikblenecnd | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 422 | draft-jochcjgobppeocmi | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | com, hanwhawm, hanwhawm com, ○, https | 현대차증권, ○, 현대차증권 ○, https, //www |  |
| 423 | draft-jogkaifgbcpkbloi | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 입금, 환불 입금 | 처리, 심사, 처리 심사 |  |
| 424 | draft-kkgjkgocldhfcfpa | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 78, 875, 875 78, 73, 375 | 83, 333, 83 333, 625, 416 |  |
| 425 | draft-igkhjkbnhiakhkdo | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 전화, 대표, 대표 전화, 로그인, 회원가입 | 일, 24, 일 24, 시간, 예약가능 |  |
| 426 | draft-gjnlciobngdjceia | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2025-12-12 |  |
| 427 | draft-mogpjaanmkfppehd | EMAIL | EMAIL | customer_support | public_web_context | non_pii | Kim, SungHwan, SungHwan Kim, Personal, information | Tel, Copyright, Tel Copyright, ⓒ, MONTSTERFACTORY |  |
| 428 | draft-oeklhgimjlnhjind | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 상담, 상담 인증 | 발송, 접수, 발송 접수 |  |
| 429 | draft-bhfjllnjbmlahoal | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, kr, kr 이메일, 전화, co | 2, 기타, 2 기타, 기관, 개인정보침해에 |  |
| 430 | draft-jpoomgapfjhajhmo | EMAIL | EMAIL | education | public_web_context | non_pii | 이메일, 전화, 전화 이메일, 담당자, 장중원 | ▶, 이의제기, ▶ 이의제기, 불복청구, 이용자는 |  |
| 431 | draft-jgcpndmadbpkohbk | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 432 | draft-kheknbnidgnacaok | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 환불, 안내 | 확인, 심사, 확인 심사 |  |
| 433 | draft-jagmafapcfmcpfoi | EMAIL | EMAIL | general_web | public_web_context | non_pii | 주소, E-mail, E-mail 주소, 개인정보보호담당, TEL | 전라남도, 나주시, 전라남도 나주시, 전력로, 55 |  |
| 434 | draft-hdddapddamlmgajo | EMAIL | EMAIL | healthcare | public_web_context | non_pii | Tel, 연락처, 연락처 Tel, 이용진, 직책 | Fax, 제11조, Fax 제11조, 권익침해, 구제방법 |  |
| 435 | draft-ipkdgoodcmhnjcda | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, -, - 이메일, 전화, 팩스 | ※, 해당, ※ 해당, 기호에, 마우스 |  |
| 436 | draft-fhoikoaakooabnbg | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | /, 고객상담, 고객상담 /, 마곡중앙8로5길, 53 | 전자우편, org, 전자우편 org, Copyright, C |  |
| 437 | draft-boimmgmafilhodkc | PHONE | PHONE_MOBILE | education | public_web_context | non_pii | ㈜잉글리쉬앤, 신입생영어심화교육과정, 신입생영어심화교육과정 ㈜잉글리쉬앤, 기계전기팀, ○ | 2026 |  |
| 438 | draft-eipphpicpjjjeckl | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 대표번호, │, │ 대표번호, 천안시, 동남구 | │, 홈페이지, │ 홈페이지, https, //nanum |  |
| 439 | draft-cihbmfaabgmgmboo | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 화, 전, 전 화, 리더, CISO | 이메일, email, 이메일 email, protected, 개인정보 |  |
| 440 | draft-bhhpcgccpnbngenj | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 대표전화, 9, 9 대표전화, 서울특별시, 종로구 | 대표자, 채동완, 대표자 채동완, 이메일, or |  |
| 441 | draft-boplglchloplgpce | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 전화 | 전자우편, kr, 전자우편 kr, 개인정보보호, 담당자 |  |
| 442 | draft-iogjmpigddhogcml | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, 회사명, 대원미디어 | /, 대표자, / 대표자, 정동훈, 주소 |  |
| 443 | draft-kcamgeebphfdbjck | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 사업자등록번호, 손경옥, 손경옥 사업자등록번호, 대진의료재단, 분당제생병원 | 대표전화, 응급센터, 대표전화 응급센터, or, kr |  |
| 444 | draft-goheecijedjebeil | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 농협, 국민, 국민 농협, 주말/공휴일, 휴무 | PC버전, 상점정보, PC버전 상점정보, 이용안내, TOP |  |
| 445 | draft-okeljlljhgcggdha | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 상담, 상담 환불 | 확인, 접수, 확인 접수 |  |
| 446 | draft-bbhmihkaafchdhhp | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 193차, 193차 변경일, 2023-01-18, 개인정보처리방침 | 개인정보처리방침, 192차, 개인정보처리방침 192차, 변경일, 2022-11-23 |  |
| 447 | draft-dodfibbblgmlneib | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 수정일자, ·, · 수정일자, 보기, 좋아요 | --, -- --, 회사소개, 인재채용, 윤리경영 |  |
| 448 | draft-egehgokkdginkgea | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 449 | draft-kchpehpeoljflgbm | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 054, 053, 053 054, 043, 051 | 070, 080, 070 080, -, 종교 |  |
| 450 | draft-jojhgocblkmiblca | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 451 | draft-lbjgjdffkdjfkbbk | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 500, 570, 570 500, 333, 525 | 165, 791, 165 791, 189, 375 |  |
| 452 | draft-khimohefamlghnli | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | +, 팩스, 팩스 +, 전화, English | 이메일, com, 이메일 com, 콘텐츠, 관리부서 |  |
| 453 | draft-hbineilabpgideik | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2023-06-01 |  |
| 454 | draft-ndjbcplmjmabgjad | EMAIL | EMAIL | customer_support | public_web_context | non_pii | 전자우편, 1588-2336, 1588-2336 전자우편, com, 문의전화 | 문의전화, 1588-2336, 문의전화 1588-2336, 수신자부담무료전화, 기타 |  |
| 455 | draft-oomkdcfbciinaaeo | EMAIL | EMAIL | customer_support | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 상담, 상담 인증 | 발송, 접수, 발송 접수 |  |
| 456 | draft-bkgilgjalphpaoag | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 구스타브, 주식회사, 주식회사 구스타브, 2023-고양덕양구-2292, 사업자정보확인 | E-mail, com, E-mail com, ©, 내게담다 |  |
| 457 | draft-mbgijhdedmcedbab | EMAIL | EMAIL | education | public_web_context | non_pii |  | Copyright, ⓒ, Copyright ⓒ, 2018, Kukje |  |
| 458 | draft-jmifnoilfoccdjom | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 459 | draft-kmkbanfpmkhfiidn | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 460 | draft-khkgcaohipeaonhc | EMAIL | EMAIL | general_web | public_web_context | non_pii | 학사운영팀장, 교원, 교원 학사운영팀장, 02, 2204 | 02, 2204-8612, 학사운영, 학적관리, 입학처 |  |
| 461 | draft-hfjkhhgfbicbligj | EMAIL | EMAIL | healthcare | public_web_context | non_pii | Tel, 연락처, 연락처 Tel, 이용진, 직책 | Fax, ②, Fax ②, 정보주체께서는, 가톨릭관동대학교 |  |
| 462 | draft-jaiafgglbeilnmng | EMAIL | EMAIL | public_services | public_web_context | non_pii | 전자우편, 전화, 전화 전자우편 | 개인정보보호, 분야별, 개인정보보호 분야별, 담당자, 기획협력과 |  |
| 463 | draft-fnedigjblichkoeg | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 연락처, 경영지원본부, 경영지원본부 연락처, 김흥완, 팀장 | 이메일, org, 이메일 org, 성명, 김상연 |  |
| 464 | draft-bpghimkaendkfnkd | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 분당융합기술교육원, 입학문의, 입학문의 분당융합기술교육원, MENU, 학생정보시스템 | 전국, 과정문의, 전국 과정문의, 1588-2282, 예비신입생 |  |
| 465 | draft-flgnjahdnmmpbkog | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | TEL, 42-15, 42-15 TEL, 기장군, 정관읍 | /, FAX, / FAX, E-mail, com |  |
| 466 | draft-ddifdejmjkinpfmb | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 기업육성팀, CKL기업지원센터, CKL기업지원센터 기업육성팀, 콘텐츠금융지원팀, 스토리움 | 기업부설창작연구소, 한국문화기술기획평가원, 기업부설창작연구소 한국문화기술기획평가원, 경영지원팀, 콘텐츠수출마케팅플랫폼 |  |
| 467 | draft-bmnjgfkebakfaieb | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 대표번호, 주차안내, 주차안내 대표번호, 온라인예약, 증명서발급 | 진료안내/예약, 진료예약, 진료안내/예약 진료예약, 인터넷, 첫방문 |  |
| 468 | draft-capmjgilgpepjkal | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 56, 서초중앙로, 서초중앙로 56, 한국CPO포럼, 서울특별시 | 개인정보보호, 전문관리자, 개인정보보호 전문관리자, 교육, 운영 |  |
| 469 | draft-ioppgdcckoimegfd | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, /, / 사업자등록번호, 601, 개인정보관리책임자 | 통신판매업신고번호, 제, 통신판매업신고번호 제, 2016-서울서초-2240호, 2016-0099505 |  |
| 470 | draft-ljmdljdkbbmmbnba | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 사업자번호, 충남대학교병원, 충남대학교병원 사업자번호, 중구, 문화로 | COPYRIGHT, BY, COPYRIGHT BY, CHUNGNAM, NATIONAL |  |
| 471 | draft-hdckiglbddcjehdi | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | CENTER, CUSTOMER, CUSTOMER CENTER, Q&A, 주문조회 | 평일, 10, 평일 10, 00, ~ |  |
| 472 | draft-oknodpeojnakpmbj | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 접수, 입금 | 처리, 상담, 처리 상담 |  |
| 473 | draft-bdclhpcokdpoepfl | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 203차, 203차 변경일, 2024-01-01, 개인정보처리방침 | 개인정보처리방침, 202차, 개인정보처리방침 202차, 변경일, 2023-09-15 |  |
| 474 | draft-eaihbcpjkdihfnjd | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 해외, 국내, 국내 해외, 대소문자, 구별 | 019, 070, 019 070, -, 해외 |  |
| 475 | draft-elagieklonkdhbcm | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 476 | draft-koakaopadodoehom | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 042, 041, 041 042, 031, 032 | 055, 061, 055 061, 062, 063 |  |
| 477 | draft-kghdegndjkkliddh | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 478 | draft-lichedhiggmlkbeg | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 전화번호, 개인정보보호팀, 개인정보보호팀 전화번호, 담당부서, 담당부서 개인정보보호팀 | 개인정보관리책임자, 김철홍, 개인정보관리책임자 김철홍, 이메일, mcd |  |
| 479 | draft-koiphgfmbhmdafka | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | +, Russian, Russian +, 대표번호, 1600-8291 | /2657, 응급의료센터, /2657 응급의료센터, 야간, 1600-6119 |  |
| 480 | draft-hkljiamomaapjfkf | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2025-05-13 |  |
| 481 | draft-pjdcledkfimdalhl | EMAIL | EMAIL | customer_support | public_web_context | non_pii | /, 기술담당, 기술담당 /, 관리책임자, 이재욱 | 2 |  |
| 482 | draft-bkkifebnoglmjacb | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 예, 앞자리, 앞자리 예, 회사, 이메일 | 에서, Hong_Gildong만, 에서 Hong_Gildong만, 입력해, 주세요 |  |
| 483 | draft-neidnohcfmfheacd | EMAIL | EMAIL | education | public_web_context | non_pii | -, kr, kr -, ac, - ac | 붙임, 3, 붙임 3, 분야별, 개인정보보호 |  |
| 484 | draft-kebljmilakangpmo | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 485 | draft-kpidlpgjefnaekii | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 486 | draft-mjmofallcbnjjcga | EMAIL | EMAIL | general_web | public_web_context | non_pii | 이메일, 김철홍, 김철홍 이메일, 개인정보관리책임자, 성명 | 9 |  |
| 487 | draft-hjpliamgajnmnjcb | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 1688-7575, TEL, TEL 1688-7575, 43길, 88 | by, Asan, by Asan, Medical, Center |  |
| 488 | draft-jakelomomielehec | EMAIL | EMAIL | public_services | public_web_context | non_pii | 박상연, 기획협력과, 기획협력과 박상연, 전화, 전자우편 | -, ②, - ②, 정보주체께서는, 제1항의 |  |
| 489 | draft-gcpbggbkinbdbich | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 고객센터 | 맨위로, 이용안내, 맨위로 이용안내, 고객센터, 1 |  |
| 490 | draft-cefchkfgckmmhene | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | FAX, 1588-2854, 1588-2854 FAX, 대림동, 원광디지털대학교 | 익산캠퍼스, 54538, 익산캠퍼스 54538, 전북특별자치도, 익산시 |  |
| 491 | draft-gbmdnbgcfodnghkc | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | TEL, /, / TEL, 정관읍, 병산로 | /, FAX, / FAX, E-mail, com |  |
| 492 | draft-dffhljpkjmpkhimh | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 주임, 김자연, 김자연 주임, 김정욱, 부장 | ERP, 전사적자원관리시스템, ERP 전사적자원관리시스템, 허강, 부장 |  |
| 493 | draft-boaljjnpamdbjngd | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 대표번호, 주차안내, 주차안내 대표번호, 온라인예약, 증명서발급 | 병원안내, 병원소식, 병원안내 병원소식, 소식/공지, 언론보도 |  |
| 494 | draft-cfpnjgedehoheppf | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 엑스, 카카오스토리 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 495 | draft-jongefmmednldoln | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 1-1호, 1-1호 사업자등록번호, 한강로3가, 현대아이파크몰테마파크 | 통신판매업신고, 제2007-서울용산-04838호, 통신판매업신고 제2007-서울용산-04838호, 개인정보관리책임, 김기남 |  |
| 496 | draft-miinbcnmflbkfbml | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | healthcare | public_web_context | non_pii | 사업자등록번호, 김춘복, 김춘복 사업자등록번호, 성광의료재단, 차움의원 | 성광의료재단, 서울특별시, 성광의료재단 서울특별시, 강남구, 도산대로 |  |
| 497 | draft-helndjebognjaojd | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 근로자들, 스리랑카, 스리랑카 근로자들, 구미보, 나들이 | 외국인근로자, 쌀, 외국인근로자 쌀, 나눔, 행사 |  |
| 498 | draft-plapmelgpbmbadge | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 상담, 상담 환불 | 확인, 접수, 확인 접수 |  |
| 499 | draft-beaijenpfdheookl | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 방침은, 본, 본 방침은, 개인정보, 처리방침 | 부터, 시행합니다, 부터 시행합니다 |  |
| 500 | draft-eapmnfhadmioinhk | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 휴대전화, *, * 휴대전화, 예정, 고교명 | -, - -, *, 주소, 검색 |  |
| 501 | draft-fakffjkmgplccnlf | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 502 | draft-mconkaekjdallhnl | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 휴대폰번호 | 031, 032, 031 032, 033, 041 |  |
| 503 | draft-knggepflpkjhnbne | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 504 | draft-mpbjppmejkfhbhmb | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 153, 605, 605 153, 861, 580 | 750, 500, 750 500, 165, 791 |  |
| 505 | draft-lcibojofoaajefda | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 선택, 날짜, 날짜 선택, STEP, 2 | 토, 12, 토 12, 일, 13 |  |
| 506 | draft-hnpgjiioiklcdlff | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 최종수정일, 전화번호, 전화번호 최종수정일, 정보, 담당부서 | 배너모음, 여성긴급전화1366, 배너모음 여성긴급전화1366, 경기북부, 정부24 |  |
| 507 | draft-cbpikhfcknncdphd | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 1833-2570, 고객센터, 고객센터 1833-2570, 브랜드관, 떨이몰 | 평일, 10, 평일 10, 00, ~ |  |
| 508 | draft-ojeibgefodmbgcgo | EMAIL | EMAIL | education | public_web_context | non_pii | to, mail, mail to, For, more | Ok, Korean, Ok Korean, English, Chinese |  |
| 509 | draft-kkadbgfckhbbpahb | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 510 | draft-lmcopbjdokgbbodd | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 환불, 안내 | 확인, 심사, 확인 심사 |  |
| 511 | draft-mmbdhakicfhkoejd | EMAIL | EMAIL | general_web | public_web_context | non_pii | 이메일, 김철홍, 김철홍 이메일, 고객센터, 개인정보관리책임자 | 기타, 개인정보침해에, 기타 개인정보침해에, 대한, 신고나 |  |
| 512 | draft-idmbmmhbppdmdkeg | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 책임자, 책임자 이메일, 전화번호, 02 | 환자서비스, 관련, 환자서비스 관련, 개인정보, 관리 |  |
| 513 | draft-jgmelbopbgmbendk | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, ·, · 이메일, 전화, 팩스 | -, 개인정보보호, - 개인정보보호, 자율점검, 지원시스템 |  |
| 514 | draft-hhkdnakbobhdjbed | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | net, 양원영, 양원영 net, 개인정보, 보호책임자 | 개인정보보호, 담당부서, 개인정보보호 담당부서, IT보안인프라팀, 정연종 |  |
| 515 | draft-chcajineobamlbgg | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | TEL, 20, 20 TEL, 전주시, 덕진구 | 한국폴리텍대학, 보이는, 한국폴리텍대학 보이는, ARS, 이용은 |  |
| 516 | draft-hlkbbhkdnbomfbfj | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 팩스, 1588-0037, 1588-0037 팩스, 30, 대표전화 | Copyright, c, Copyright c, KDIC, All |  |
| 517 | draft-dfgdimfcnmjepjib | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 정보보안팀, 관리시스템, 관리시스템 정보보안팀, ERP, 전사적자원 | 대중문화예술종합정보시스템, 대중음악산업팀, 대중문화예술종합정보시스템 대중음악산업팀, 콘텐츠분쟁조정위원회, 공정상생센터 |  |
| 518 | draft-cckdhkamkligkcgj | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | FAX, 1899-0000, 1899-0000 FAX, 제봉로, 42 | COPYRIGHT, ⓒ, COPYRIGHT ⓒ, 2018, CNUH |  |
| 519 | draft-ciadeljhjbbomfph | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 팩스, -, - 팩스, 박상연, 전화 | -, 이메일, - 이메일, kr, ② |  |
| 520 | draft-kcblojcofidkbaki | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 고객센터, 고객센터 사업자등록번호, 제휴문의, -- | 통신판매업신고, 2022-서울강서-1657, 통신판매업신고 2022-서울강서-1657, 재단법인, 행복에프앤씨 |  |
| 521 | draft-jghefepmfkajiljc | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 입금안내, 무통장, 무통장 입금안내, 30, 주말·공휴일 | 기업은행, 주, 기업은행 주, 제이에스벤처스, 이용안내 |  |
| 522 | draft-bipldilpkgkoknnh | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | ~, 2024-04-03, 2024-04-03 ~, 서비스, 운영 | 인증번호, ISMS-KISA-2024-033, 인증번호 ISMS-KISA-2024-033, 인증범위, 맘큐 |  |
| 523 | draft-ebclagengdmhnfeg | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 선택, *, * 선택, --, 휴대전화 | 019, -, 019 -, 이메일주소, * |  |
| 524 | draft-fcpnpbmfjidnhjcp | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 525 | draft-nbhkglcflplkfegj | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 062, 061, 061 062, 053, 054 | 휴대전화, 010, 휴대전화 010, 011, 016 |  |
| 526 | draft-lgndjjghhfmajidj | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 입금, 환불 입금 | 처리, 심사, 처리 심사 |  |
| 527 | draft-okpbopfgocaacela | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 104, 625, 625 104, 574, 333 | 595, 769, 595 769, 112, 269 |  |
| 528 | draft-lpebgiabnedecapn | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | +, 전화, 전화 +, 국제성모병원, 국제진료센터 | English, Russian, English Russian, 팩스, 이메일 |  |
| 529 | draft-iaemnmjcmkgfnefp | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2016-10-05 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 530 | draft-ccjedcobldkiibdd | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 고객센터, 담당부서, 담당부서 고객센터, IT보안인프라팀, 정연종 | 1833-2570, ②, 1833-2570 ②, 정보주체는, 회사의 |  |
| 531 | draft-pbdaomjfjnnkfgdk | EMAIL | EMAIL | education | public_web_context | non_pii | 이메일, 전화번호, 전화번호 이메일, 범, 희 | 부서명, 사무처, 부서명 사무처, 성명, 장 |  |
| 532 | draft-klemdcbkmmejpkpd | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 533 | draft-mikddgecodcbajek | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 환불, 안내 | 확인, 심사, 확인 심사 |  |
| 534 | draft-mmolbgkmfomkefnm | EMAIL | EMAIL | general_web | public_web_context | non_pii | 일, 메, 메 일, -, 전화번호 | 13 |  |
| 535 | draft-jlalfnpmpflcplfn | EMAIL | EMAIL | healthcare | public_web_context | non_pii | e-mail, -, - e-mail, 전화번호, 032 | 제12조, 고정형, 제12조 고정형, 영상정보처리기기, 운영·관리에 |  |
| 536 | draft-kcfkbgepbahhcoha | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, ·, · 이메일, 전화, 팩스 | 자율보호, 정책과, 자율보호 정책과, -, 개인정보 |  |
| 537 | draft-hicmibpbkoofkmeb | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 전화번호, net, net 전화번호, 담당자, 정연종 | 제11조, 고객의, 제11조 고객의, 권리와, 의무 |  |
| 538 | draft-cncfmdlalahckeje | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 경리구매팀, 발송, 발송 경리구매팀, 내역, 확인 | 4, 입학전형, 4 입학전형, 한국대학교육협의회, ㈜유웨이어플라이 |  |
| 539 | draft-ilnaopgcnfdoohof | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 대표전화, 30, 30 대표전화, 서울시, 중구 | 고객센터, 1588-0037, 고객센터 1588-0037, 팩스, Copyright |  |
| 540 | draft-dgpaejnkkbiokahm | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 콘텐츠IP전략팀, 스토리움, 스토리움 콘텐츠IP전략팀, 콘텐츠가치평가, 시스템 | CKL기업지원센터, 기업육성팀, CKL기업지원센터 기업육성팀, 기업부설창작연구소, 한국문화기술기획평가원 |  |
| 541 | draft-ceiefcmcmkcobldl | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 응급실, 입원비확인ARS, 입원비확인ARS 응급실, 건강검진예약, 약처방문의 | 고객상담실, 장례식장, 고객상담실 장례식장, 진료의뢰·협력, -- |  |
| 542 | draft-ckcoljjlclmkiioa | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 박영수, 유출신고, 유출신고 박영수, 전문강사, 윤여진 | 분쟁조정과장, 분쟁조정, 분쟁조정과장 분쟁조정, 이정아, 개인정보 |  |
| 543 | draft-lgbcknmaoichhcmd | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 607호, 607호 사업자등록번호, One, 파크원 | 통신판매업신고, 2023-고양덕양구-2292, 통신판매업신고 2023-고양덕양구-2292, 사업자정보확인, 개인정보보호책임자 |  |
| 544 | draft-kcopknghcodjokcb | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 대해서, f-3비자에, f-3비자에 대해서, 참여, 안내 | G1, 비자에, G1 비자에, 대한, 이해 |  |
| 545 | draft-bmkjjbgefhoakmpc | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 전화번호, 경영지원실, 경영지원실 전화번호, 성명, 김도균 | 이메일, co, 이메일 co, kr, o |  |
| 546 | draft-efgapndnifaiacjc | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii |  | Q&A, 애니메이션으로, Q&A 애니메이션으로, 배우는, 중국어 |  |
| 547 | draft-foohebmipongghnp | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 548 | draft-odllbpobbbpmfhdo | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 02, 019, 019 02, 010, 011 | 043, 051, 043 051, 052, 053 |  |
| 549 | draft-lhehajeenpcplmfa | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 입금, 환불 입금 | 처리, 심사, 처리 심사 |  |
| 550 | draft-piegapeppiahapin | BANK_ACCOUNT | BANK_ACCOUNT | general_web | public_web_context | non_pii | 241, 241 241, 341, 605, 571 | 605, 153, 605 153, 333, 525 |  |
| 551 | draft-mbmkfmeeenhbbach | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 경보제약, 2024-12-31, 2024-12-31 경보제약, PCA, 약물용량 | 수술, 후, 수술 후, 통증, 감소를 |  |
| 552 | draft-ifaiijkbhdgihlaf | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2023-05-22 |  |
| 553 | draft-cgodacamhjmiodjc | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 메일, 김기남, 김기남 메일, 애니메이트, 온라인샵 | ※메일로, 문의시, ※메일로 문의시, 답변, 및 |  |
| 554 | draft-pdbiehkkpnjffhki | EMAIL | EMAIL | education | public_web_context | non_pii | mark_email_read, phone_android, phone_android mark_email_read, 1, 서울대학교 | COPYRIGHT, C, COPYRIGHT C, 2021, FoodTech |  |
| 555 | draft-kljmchpfdapphnpp | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 556 | draft-nfhdlipjphgbnjoi | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 환불, 안내 | 확인, 심사, 확인 심사 |  |
| 557 | draft-moobikbghlhcohkg | EMAIL | EMAIL | general_web | public_web_context | non_pii | 정보지원팀장, 책임자, 책임자 정보지원팀장, 정보처, 정보처장 | 02, 2204, 02 2204, 8049, 정보지원 |  |
| 558 | draft-jlghhhdjeggbklbm | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 책임자, 책임자 이메일, 전화번호, 02 | 소하검진센터, 개인정보, 소하검진센터 개인정보, 관리, 부서 |  |
| 559 | draft-knaipfmihlemeoin | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, -, - 이메일, 전화, 팩스 | ②, 정보주체께서는, ② 정보주체께서는, 제1항의, 열람청구 |  |
| 560 | draft-hkbpebhobjmljpop | PHONE | PHONE_MOBILE | ecommerce | public_web_context | non_pii | 주문, 문자, 문자 주문, 📌, 📌 문자 | 문자, 전용, 문자 전용 |  |
| 561 | draft-ddapjdfjpgefbnmc | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 에듀메이커스, 캠프’, 캠프’ 에듀메이커스, B, T | 2026 |  |
| 562 | draft-imajkhjnjiidfkbg | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | FAX, /, / FAX, 병산로, 42-15 | E-mail, com, E-mail com, COPYRIGHT, C |  |
| 563 | draft-dpjpealpldbplfhl | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 게임기반조성팀, ​모바일/VR게임테스트베드, ​모바일/VR게임테스트베드 게임기반조성팀, 공정상생센터, 게임국가기술자격검정 | 이행, 콘텐츠가치평가시스템, 이행 콘텐츠가치평가시스템, 콘텐츠금융지원팀, 스토리움 |  |
| 564 | draft-cgbmkdoiapndjneb | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 고객상담실, 응급실, 응급실 고객상담실, 약처방문의, 약처방전재발급 | 장례식장, 진료의뢰·협력, 장례식장 진료의뢰·협력, --, 홈페이지/앱이용문의 |  |
| 565 | draft-ckppefnhakkpelki | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 전화, ·, · 전화, 사용자, 정보 | ·, 팩스, · 팩스, 이메일, kr |  |
| 566 | draft-mbjgjnjkbbpmamba | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 정동훈, 정동훈 사업자등록번호, 이용약관, 고객센터 | 서울특별시, 용산구, 서울특별시 용산구, 한강대로23길, 55 |  |
| 567 | draft-khjdinckflbfnmho | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 국민은행, 우수패밀리, 우수패밀리 국민은행, Info, 예금주 | 주식회사, 우수패밀리, 주식회사 우수패밀리, 대표, 노인석 |  |
| 568 | draft-bogakkpjibagaegp | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 1-, com, com 1- | 미국, 성명, 미국 성명, 성별, 생년월일 |  |
| 569 | draft-ehdllhkpmmjppbka | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 해외전화, 1588-2854, 1588-2854 해외전화, 입학자료신청, 입학상담 | -0010, 입학상담, -0010 입학상담, 1번, 시간제 |  |
| 570 | draft-ghkjddkdmefjjicj | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 571 | draft-ophkckcpdddojjid | BANK_ACCOUNT | BANK_ACCOUNT | finance | public_web_context | non_pii | 041, 033, 033 041, 02, 031 | 053, 054, 053 054, 055, 061 |  |
| 572 | draft-mlikgfmpfdbeaamh | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 입금, 환불 입금 | 처리, 심사, 처리 심사 |  |
| 573 | draft-mbmnmdpaonplmpdi | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 등, 약물용량, 약물용량 등, 신장, 체중 | 경보제약, 8, 경보제약 8, 개인정보의, 자동 |  |
| 574 | draft-iojmdkifojmnknff | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2025-07-31 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 575 | draft-ckhoaedcmjbohhel | EMAIL | EMAIL | ecommerce | public_web_context | non_pii |  | /, 미국, / 미국, 성명, 성별 |  |
| 576 | draft-pncbpmidiffjolah | EMAIL | EMAIL | education | public_web_context | non_pii | 문의, 사전, 사전 문의, 또는, 전화 | +82-2-944-5000, 01133, 서울특별시, 강북구, 솔매로49길 |  |
| 577 | draft-lepjpbjflbgbmmah | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 578 | draft-nincanmfdeibmbcc | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 환불, 안내 | 확인, 심사, 확인 심사 |  |
| 579 | draft-mpnkaamaljpopdaf | EMAIL | EMAIL | general_web | public_web_context | non_pii | 1301, 국번없이, 국번없이 1301, kr, 대검찰청 | http, //spo, http //spo, go, kr |  |
| 580 | draft-jnjhnmiidcdknalm | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 책임자, 책임자 이메일, 전화번호, 02 | 모바일앱, 개인정보, 모바일앱 개인정보, 관리, 부서 |  |
| 581 | draft-kniemhopcpalmace | EMAIL | EMAIL | public_services | public_web_context | non_pii | 1301, 국번없이, 국번없이 1301, ▶, 대검찰청 | www, spo, www spo, go, kr |  |
| 582 | draft-incjobpagccklnlf | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 전화번호, 지피클럽, 지피클럽 전화번호, 성명, 안병근 | 이메일, G법3, 이메일 G법3, gpmd, co |  |
| 583 | draft-dfoelfhlpfjkmila | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | FAX, 1588-2282, 1588-2282 FAX, 보이는, ARS | COPYRIGHT, 2010, COPYRIGHT 2010, BY, KOREA |  |
| 584 | draft-jejbpfdfaimlelhn | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | com, //kakaopaysec, //kakaopaysec com, ○, X | 우리투자증권, ○, 우리투자증권 ○, X, www |  |
| 585 | draft-eaogeobkakcppgji | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 연락처, 정보지원팀원, 정보지원팀원 연락처, 직위, 정보처 | 8089, E-Mail, 8089 E-Mail, privacy, ac |  |
| 586 | draft-ckkimcghphbcpgep | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | VIP종합건강증진센터, 건강관리센터, 건강관리센터 VIP종합건강증진센터, 1600-8291, 응급의료센터 | ~8, 특수건강진단, ~8 특수건강진단, 오시는길, 층별안내 |  |
| 587 | draft-dbaipmhhfookbjab | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 주민과, 행정안전부, 행정안전부 주민과, 제도를, 담당하는 | 위, 담당부서와, 위 담당부서와, 전화번호는, 이 |  |
| 588 | draft-mmnaiepcdmmpmbdk | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, com, com 사업자등록번호, TEL, 1833-2570 | 사업자번호조회, 통신판매업신고번호, 사업자번호조회 통신판매업신고번호, 제, 2026-서울성동-0130 |  |
| 589 | draft-kplneaabphbabpmo | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 한글교실, 3월, 3월 한글교실, 구미시, 자원순환과 | 3월, 한글교실, 3월 한글교실, 2026-02-27, 외국인 |  |
| 590 | draft-cbmblbmhnckkcaph | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 165차, 165차 변경일, 2020-09-29, 개인정보처리방침 | 개인정보처리방침, 164차, 개인정보처리방침 164차, 변경일, 2020-09-01 |  |
| 591 | draft-ejopljabmejjkbdf | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 1975, 1976, 1976 1975, 1979, 1978 | 1969, 1968, 1969 1968, 1967, 1966 |  |
| 592 | draft-hbllhehbogjifgio | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 593 | draft-mmhpooblemcocpgi | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 594 | draft-mhjekpcfkjfihnml | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 선택, 입력, 입력 선택, 휴대폰번호, 필수 | 019, -, 019 -, 희망, 진료과 |  |
| 595 | draft-jkonckbpchcmamef | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2023-06-01 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 596 | draft-dbhignkejbakgmnf | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 전화번호, 전화번호 이메일, 온라인, 화장품 | o, 개인정보, o 개인정보, 보호책임자, 성명 |  |
| 597 | draft-mbjbpdmiiandoadh | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 598 | draft-nkmdhhnmegjhmggj | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 599 | draft-nigpacgimofcnkho | EMAIL | EMAIL | general_web | public_web_context | non_pii | E-Mail, •, • E-Mail, 전화번호, 8089 | •, 운영시간, • 운영시간, 월~금, 09 |  |
| 600 | draft-kchkdgomioodmpcp | EMAIL | EMAIL | healthcare | public_web_context | non_pii | E-mail | 2, 회신, 2 회신, 및, 진료 |  |
| 601 | draft-kpecblcdpbchclda | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, 전화, 전화 이메일, 이혜림, - | 팩스, ③, 팩스 ③, ｢개인정보, 보호법｣ |  |
| 602 | draft-inhifkbldfdniabg | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | /, kr, kr /, //www, spo | 경찰청, 사이버안전국, 경찰청 사이버안전국, http, //cyberbureau |  |
| 603 | draft-dmmmnmeaoppfbijm | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 상담 | 교내, 연락처, 교내 연락처, 바로가기, 입학 |  |
| 604 | draft-jflngckikhbhanbi | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 대표전화, 30, 30 대표전화, 서울시, 중구 | 고객센터, 1588-0037, 고객센터 1588-0037, 팩스, Copyright |  |
| 605 | draft-edhihbbmeeilgdgd | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | /, kr, kr /, http, //spo | 경찰청, 사이버테러대응센터, 경찰청 사이버테러대응센터, www, netan |  |
| 606 | draft-ckngbbbgmdmjpmdj | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 문의, 00, 00 문의, ~, 13 | 월~금, 08, 월~금 08, 00, ~ |  |
| 607 | draft-dbkmpjpcfnmghkkk | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 전화 | 전자우편, kr, 전자우편 kr, 개인정보보호, 분야별 |  |
| 608 | draft-piakicdjocmanlmg | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 김정웅, 김정웅 사업자등록번호, 주, 지피클럽 | 사업자정보확인, 통신판매업신고번호, 사업자정보확인 통신판매업신고번호, 2022-서울용산-1045, TEL |  |
| 609 | draft-lmninmejkcaacflk | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 안내, 신청, 신청 안내, E-7-4, 체류자경 | 마약청정, 대한민국, 마약청정 대한민국, 2026-04-24, 광역형비자 |  |
| 610 | draft-ccjibebmmcbempnd | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 186차, 186차 변경일, 2022-06-29, 개인정보처리방침 | 개인정보처리방침, 185차, 개인정보처리방침 185차, 변경일, 2022-04-20 |  |
| 611 | draft-fbdoehcmalofailb | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 2005, 2006, 2006 2005, 2009, 2008 | 1999, 1998, 1999 1998, 1997, 1996 |  |
| 612 | draft-hcbkgjokdjjaiclc | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 613 | draft-negmbdnngjlbapbn | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 614 | draft-mmkhphhbcimkigic | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 연락처, 이름, 이름 연락처 | 019, -, 019 -, 생년월일, 성별 |  |
| 615 | draft-jpoageokeejgklhd | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2025-10-29 |  |
| 616 | draft-deonldcgappcaglj | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 전화, 전화 이메일, 유한킴벌리, 고객지원센터 | 이메일, co, 이메일 co, kr, 2 |  |
| 617 | draft-mdbdogmbponhkjle | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 618 | draft-olabebmifhfognoa | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 환불, 안내 | 확인, 심사, 확인 심사 |  |
| 619 | draft-niobdpiopopmeahc | EMAIL | EMAIL | general_web | public_web_context | non_pii | 이메일, 6316, 6316 이메일, 정보보안팀, 연락처 | 닫기, 레이어팝업닫기, 닫기 레이어팝업닫기, *, 기호를 |  |
| 620 | draft-kghjgdlamfepefma | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, -, - 이메일, 전화번호, 032 | ※, 자세한, ※ 자세한, 내용은, 개인정보 |  |
| 621 | draft-mhplgmhkiodgpppe | EMAIL | EMAIL | public_services | public_web_context | non_pii | 전자우편, 전화, 전화 전자우편 | 개인정보보호, 담당자, 개인정보보호 담당자, 기획협력과, 이상화 |  |
| 622 | draft-ipeagjpmmfnkhlac | PHONE | PHONE_MOBILE | ecommerce | public_web_context | non_pii | 주문, 문자, 문자 주문, 📌, 📌 문자 | 문자, 전용, 문자 전용 |  |
| 623 | draft-dojgnkpeflcefpfj | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | TEL, 112, 112 TEL, 서울특별시, 강서구 | 한국폴리텍대학, 보이는, 한국폴리텍대학 보이는, ARS, 이용은 |  |
| 624 | draft-jklhmpjfllinlkpe | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 팩스, 1588-0037, 1588-0037 팩스, 30, 대표전화 | Copyright, c, Copyright c, KDIC, All |  |
| 625 | draft-egjcllkkcninlcnb | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 게임유통팀, 게임더하기, 게임더하기 게임유통팀, 없음, 이행 | 홈페이지, 유지, 홈페이지 유지, 관리, 웹사이트 |  |
| 626 | draft-cmmgijmedokgopol | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 문의사항, 변동됩니다, 변동됩니다 문의사항, 부수에, 따라 | 동의서, 및, 동의서 및, 위임장, 다운로드 |  |
| 627 | draft-dcoeafobdagagppl | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 당직실, ※, ※ 당직실 | ~2, 평일, ~2 평일, 18시, ~ |  |
| 628 | draft-pldipiccohdlkode | REGISTRATION_IDENTIFIER | BUSINESS_REG_NO | ecommerce | public_web_context | non_pii | 사업자등록번호, 이랜드글로벌R&D센터, 이랜드글로벌R&D센터 사업자등록번호, 마곡동로, 146 | 통신판매업신고번호, 제2025-서울강서-2260, 통신판매업신고번호 제2025-서울강서-2260, 개인정보보호책임자, 민혜정 |  |
| 629 | draft-ndlphdiahmalljgg | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 한글교실, 3월, 3월 한글교실, 2026-02-27, 한글교실 2026-02-27 | 외국인, 근로자, 외국인 근로자, 한글교실, 2026-02-27 |  |
| 630 | draft-cfnnnjacafjdhlgb | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 190차, 190차 변경일, 2022-10-24, 개인정보처리방침 | 개인정보처리방침, 189차, 개인정보처리방침 189차, 변경일, 2022-08-26 |  |
| 631 | draft-fbmflgncmjipneao | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 선택, 모, 모 선택, 보호자, 연락처 | 019, 070, 019 070, -, 입학동기 |  |
| 632 | draft-hhholhbgkeaknbab | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 633 | draft-nijfljcogbcompae | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 634 | draft-njgednfnockdcknh | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 018, 017, 017 018, 010, 011 | 서울, 031, 서울 031, 경기, 032 |  |
| 635 | draft-ldehgedgnocmpacm | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2025-12-12 |  |
| 636 | draft-difdbplfopcknimf | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 1544-3800, 1544-3800 이메일, 직위, 본부장 | 개인정보, 고충처리, 개인정보 고충처리, 담당부서, 고객만족센터 |  |
| 637 | draft-mdbmlafbdbcodfnp | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 638 | draft-olmepngbpdnlcmbh | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 639 | draft-nodfilfabckmodlc | EMAIL | EMAIL | general_web | public_web_context | non_pii | 이메일, 김철홍, 김철홍 이메일, 개인정보관리책임자, 성명 | 10 |  |
| 640 | draft-kgikllmgkhhakfai | EMAIL | EMAIL | healthcare | public_web_context | non_pii | e-mail, -, - e-mail, 전화번호, 032 | 개인정보보호, 담당자, 개인정보보호 담당자, -, 부서 |  |
| 641 | draft-mifodgmogiepabjn | EMAIL | EMAIL | public_services | public_web_context | non_pii | 박상연, 기획협력과, 기획협력과 박상연, 전화, 전자우편 | -, ①, - ①, 정보주체는, 「개인정보 |  |
| 642 | draft-kflopdbalhaonafd | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 팩스, com, com 팩스, KIM, DO | _imgTag_, 쿠폰존, _imgTag_ 쿠폰존, n, 사은품 |  |
| 643 | draft-ehminipmdaiaioaf | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | kr, ac, ac kr, 총무관리처, 총무팀 | 제6조, 개인정보의, 제6조 개인정보의, 파기, ① |  |
| 644 | draft-kmihbhbeeahegjhl | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 팩스, 1588-0037, 1588-0037 팩스, 30, 대표전화 | Copyright, c, Copyright c, KDIC, All |  |
| 645 | draft-ejinfnpeiokgkmco | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 팩스, 전화, 전화 팩스, 강한승, 부장 | 주소, 전라남도, 주소 전라남도, 나주시, 전력로 |  |
| 646 | draft-cmoefojoemmiamci | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | ☎ | Q, 출력테스트, Q 출력테스트, 시, 등록되지 |  |
| 647 | draft-dcpjhkchmppnhknd | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii |  | ※, 당직실, ※ 당직실, 평일, 18시 |  |
| 648 | draft-nfokhoalbijkgkln | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 나들이, 구미보, 구미보 나들이, 2026-05-10, 필리핀 | 스리랑카, 근로자들, 스리랑카 근로자들, 2026-03-08, 외국인근로자 |  |
| 649 | draft-cgfikdhcjmncbebd | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 2023-, 2025-03-19, 확인, 2026-05-11, 2025-09-20 | 2023-03-14, 공식, 2023-03-14 공식, 굿즈, 브랜드관 |  |
| 650 | draft-fbnbmomcjagodhdg | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 건, 문의의, 문의의 건, 우편발급, 홈페이지 | RE, 성적증명서, RE 성적증명서, 우편발급, 홈페이지 |  |
| 651 | draft-hideppdejpkjfhhm | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 652 | draft-odmhnfnicdjjgflb | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 653 | draft-oakmbingmhafboof | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 선택, 00, 00 선택, 10, ~ | 019, -, 019 -, 신청, 휴대폰 |  |
| 654 | draft-ldpghopigemkhbgi | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 기타정보, 최근 | --, 바로가기, -- 바로가기, 전자결제, 안내 |  |
| 655 | draft-dikigddbfajjkaic | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 개인정보처리담당자, -, - 개인정보처리담당자, 개인정보, 관련 | -, 전화번호, - 전화번호, 국번없이, 1599-0110 |  |
| 656 | draft-miebejpkjcefeaod | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 657 | draft-pbbbiijfpkkkflno | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 인증, 인증 이메일, 심사, 심사 인증 | 발송, 환불, 발송 환불 |  |
| 658 | draft-oemhofoklejfddel | EMAIL | EMAIL | general_web | public_web_context | non_pii | 이메일, 김철홍, 김철홍 이메일, 개인정보보호팀, 전화번호 | 기타, 개인정보침해에, 기타 개인정보침해에, 대한, 신고나 |  |
| 659 | draft-kpidkacfghikfeia | EMAIL | EMAIL | healthcare | public_web_context | non_pii | Tel, 연락처, 연락처 Tel, 보호책임자, 성명 | Fax, ※, Fax ※, 개인정보, 보호 |  |
| 660 | draft-nahpakcadpmhcaae | EMAIL | EMAIL | public_services | public_web_context | non_pii | 전자우편, 전화, 전화 전자우편 | 개인정보보호, 담당자, 개인정보보호 담당자, 기획협력과, 이상화 |  |
| 661 | draft-kjcgmciigffilonb | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 전화, 2020-서울마포-2540, 2020-서울마포-2540 전화, 사업자등록번호, 사업자정보확인 | ※온라인, 문의는, ※온라인 문의는, 전화로, 접수받지 |  |
| 662 | draft-elicddnkjgnlpogn | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii |  | E-Mail |  |
| 663 | draft-ldokipgjpehlcbch | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | kr, co, co kr, http, //www | 코리아에셋투자증권, ○, 코리아에셋투자증권 ○, X, http |  |
| 664 | draft-emjnpljcnmeihigg | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 공정상생센터, 콘텐츠분쟁조정위원회, 콘텐츠분쟁조정위원회 공정상생센터, 정보보안팀, 대중문화예술종합정보시스템 | 게임국가기술, 자격검정, 게임국가기술 자격검정, 게임기반조성팀, ​모바일/VR게임테스트베드 |  |
| 665 | draft-cooihfhoiigohkmg | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 취소, 및, 및 취소, 문의전화, 입원예약 | 병상배정, 확인, 병상배정 확인, 1688-7575, ARS |  |
| 666 | draft-dladgnioocbfjocm | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 민방위비상대비교육과, 재난안전교육과, 재난안전교육과 민방위비상대비교육과, 00-18, 00 | COPYRIGHT, C, COPYRIGHT C, National, Disaster |  |
| 667 | draft-nhkobgfmlidlnpfk | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 한글교실, 근로자, 근로자 한글교실, 2026-02-27, 외국인 | 외국인, 주민, 외국인 주민, 한글교육생, 모집 |  |
| 668 | draft-cjcbkibihdleaefk | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 전화, 고객지원센터, 고객지원센터 전화, 배현정, 부서명 | 전화, 이메일, 전화 이메일, co, kr |  |
| 669 | draft-fcaechcomcaejjpo | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii |  | 시스템, 정기, 시스템 정기, 예방점검, 안내 |  |
| 670 | draft-hmlekgjoadbnjmmn | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 671 | draft-olaemielffmiafad | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 입금, 환불 입금 | 처리, 심사, 처리 심사 |  |
| 672 | draft-ocapkdcehggkblpo | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 연락처, 이름, 이름 연락처, 건강검진, 상담 | 019, -, 019 -, 생년월일, 국외 |  |
| 673 | draft-lenbkkdoelhbknjf | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2026-01-26 |  |
| 674 | draft-djbidnbnbijhmbne | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 전화번호, 전화번호 이메일, 황한별, 소속 | o, 개인정보, o 개인정보, 보호책임자, 성명 |  |
| 675 | draft-njhpaeikhmhlpdpj | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 676 | draft-pkpfgiekcfbaageb | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 환불, 안내 | 확인, 심사, 확인 심사 |  |
| 677 | draft-oghdkgppdfffkbhh | EMAIL | EMAIL | general_web | public_web_context | non_pii | 총무팀장, 행정지원처장, 행정지원처장 총무팀장, 졸업생관리, 상담 | 02, 22034-8006, 총무, 재무, 대학원 |  |
| 678 | draft-lgbhmbbhpnkoebbg | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 대표, 대표 이메일, 장기려로, 262 | 대표, 전화, 대표 전화, 991-0675, 영육치료 |  |
| 679 | draft-naoedkedcgiaplbn | EMAIL | EMAIL | public_services | public_web_context | non_pii | 전자우편, 전화, 전화 전자우편 | 개인정보보호, 담당자, 개인정보보호 담당자, 기획협력과, 박상연 |  |
| 680 | draft-lphpdldeonfapkji | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | TEL, 2016-0099505, 2016-0099505 TEL, 제, 2016-서울서초-2240호 | /, FAX, / FAX, 이메일, com |  |
| 681 | draft-enomofhmhfbmchjl | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii |  | 팩스번호 |  |
| 682 | draft-lpfbiffahlinmlgm | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | kr, co, co kr, http, //www | 한국증권금융, ○, 한국증권금융 ○, X, http |  |
| 683 | draft-emlhkapcpoppndlp | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 과장, 정철우, 정철우 과장, 부장, 대중문화예술종합정보시스템 | 콘텐츠분쟁조정위원회, 공정상생센터, 콘텐츠분쟁조정위원회 공정상생센터, 선지혜, 과장 |  |
| 684 | draft-cppabhpkeadpacle | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 특수건강진단, VIP종합건강증진센터, VIP종합건강증진센터 특수건강진단, 응급의료센터, 1600-6119 | 오시는길, 층별안내, 오시는길 층별안내, 증명서발급, 안내 |  |
| 685 | draft-dmoamojbmllfifgf | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 가름로, 143 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 686 | draft-npofeamapephlkaf | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 자원순환과, 구미시, 구미시 자원순환과, 올바른, 분리배출 | 3월, 한글교실, 3월 한글교실, 2026-02-27, 한글교실 2026-02-27 |  |
| 687 | draft-cooclcpnagjdmehn | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 1-, /, / 1-, com, com / | 미국, 성명, 미국 성명, 성별, 생년월일 |  |
| 688 | draft-fdmeppejggobagfn | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | ㈜퓨쳐누리, 대행, 대행 ㈜퓨쳐누리, 중앙도서관, 운영시스템 |  |  |
| 689 | draft-hpdhcbihggcjbenk | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 690 | draft-pibkgmmjmiomceje | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 691 | draft-ockocjbnnmibmbpc | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | +, English, English +, 국제진료센터, 1층 | /2657, Russian, /2657 Russian, 팩스, 이메일 |  |
| 692 | draft-mikifgipaagfgnef | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2025-07-31 |  |
| 693 | draft-dpmkkliebhpgefab | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 문의, 제휴, 제휴 문의, 공휴일, 제외 | 수출, 제휴, 수출 제휴, 문의, com |  |
| 694 | draft-njlbkdodnhhjjind | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 695 | draft-plkcfcdfpenhdhgf | EMAIL | EMAIL | finance | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 환불, 안내 | 확인, 심사, 확인 심사 |  |
| 696 | draft-onponboeolcihhgi | EMAIL | EMAIL | general_web | public_web_context | non_pii | 이메일, 팩스, 팩스 이메일, 대표자, 신구 | 등록번호, 제2013-서울광진-0147호, 등록번호 제2013-서울광진-0147호, 고유번호, 2023 |  |
| 697 | draft-ljbbbphhkghkijge | EMAIL | EMAIL | healthcare | public_web_context | non_pii | e-mail, 7000, 7000 e-mail, 02, 2276 | 법인명, 서울특별시, 법인명 서울특별시, 서울의료원, 사업자 |  |
| 698 | draft-nbokblpapdlgohhp | EMAIL | EMAIL | public_services | public_web_context | non_pii | 전자우편, 팩스, 팩스 전자우편, 전화, 전화 팩스 | 개인정보보호, 담당자, 개인정보보호 담당자, 기획협력과, 이상화 |  |
| 699 | draft-mpleogkhhkdnmebe | PHONE | PHONE_MOBILE | ecommerce | public_web_context | non_pii | /, com, com /, 구스타브, 대표이사 | 2, 정보주체는, 2 정보주체는, 회사의, 서비스를 |  |
| 700 | draft-epjkdedfiaknjbke | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 조성호, 총무팀, 총무팀 조성호, 이메일, 팩스 | ac, kr, ac kr, 제6조, 개인정보의 |  |
| 701 | draft-nbfjgpmeffnbgmgo | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 대표전화, 30, 30 대표전화, 서울시, 중구 | 고객센터, 1588-0037, 고객센터 1588-0037, 팩스, Copyright |  |
| 702 | draft-epdmjdjapkbkafjh | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 부원장, 유현석, 유현석 부원장, 연락처, 개인정보 | E-mail, kr, E-mail kr, Fax, 개인정보 |  |
| 703 | draft-dgbldopdohgiakpo | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 홈페이지/앱이용문의, --, -- 홈페이지/앱이용문의, 고객상담실, 장례식장 | 오시는, 길, 오시는 길, 원내위치안내, -- |  |
| 704 | draft-doedmpnkockfoifg | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 제대군인일자리과, 국가보훈부, 국가보훈부 제대군인일자리과, 제도를, 담당하는 | 위, 담당부서와, 위 담당부서와, 전화번호는, 이 |  |
| 705 | draft-oebnfbdjgimlaojm | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | Tel, kr, kr Tel, SungHwan, Kim | Copyright, ⓒ, Copyright ⓒ, MONTSTERFACTORY, ⓒ MONTSTERFACTORY |  |
| 706 | draft-cpablfihgngjgoan | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 대표전화, 고객센터, 고객센터 대표전화, 1, 1문의 | 수신자부담, 2, 수신자부담 2 |  |
| 707 | draft-ffjahcbcnggdjfdn | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 1995, 1996, 1996 1995, 1999, 1998 | 1989, 1988, 1989 1988, 1987, 1986 |  |
| 708 | draft-icaljgmjnicnelcm | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 709 | draft-pplepfoeoogokefi | BANK_ACCOUNT | BANK_ACCOUNT | finance | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 심사, 심사 환불 | 확인, 환불, 확인 환불 |  |
| 710 | draft-ogahjnbinkdgbeia | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 신한은행, 계좌번호, 계좌번호 신한은행, 입원시, 준비사항 | 한양대학교병원, 입원확인서, 한양대학교병원 입원확인서, 및, 진단서 |  |
| 711 | draft-mjeoahfoceccgcfd | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2025-07-31 |  |
| 712 | draft-efjlmichomnhkhnp | EMAIL | EMAIL | ecommerce | public_web_context | non_pii |  | 미국, 성명, 미국 성명, 성별, 생년월일 |  |
| 713 | draft-nomngnjnaocbbkjf | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 714 | draft-oojnfjhbcfbojoff | EMAIL | EMAIL | general_web | public_web_context | non_pii | 입학홍보팀장, 입학처장, 입학처장 입학홍보팀장, 학사운영, 학적관리 | 02, 2204-8605, 대학, 입시, 홍보 |  |
| 715 | draft-lmbmgcaglmniphag | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 2610-9291, 2610-9291 이메일, 의무기록팀, 전화번호 | 홈페이지, 개인정보, 홈페이지 개인정보, 관리, 부서 |  |
| 716 | draft-njgdnejamdcbfkoe | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, ·, · 이메일, 전화, 팩스 | 데이터안전, 정책과, 데이터안전 정책과, -, 가명정보 |  |
| 717 | draft-ngcncodfepmphela | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 전화, 정동훈, 정동훈 전화, 주, 대표자 | 주소, 서울특별시, 주소 서울특별시, 용산구, 한강대로23길 |  |
| 718 | draft-fdojjjfmlckkaajc | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 연락처, -, - 연락처, 담당자, 총무팀 | ②, 조선대학교는, ② 조선대학교는, 개인정보의, 적법성 |  |
| 719 | draft-pkiecnomkgaojkpb | PHONE | PHONE_LANDLINE | finance | public_web_context | non_pii | 말씀, 고객의, 고객의 말씀, 해외, +82 | 신규상담, 예적금, 신규상담 예적금, 1599-8100, 대출 |  |
| 720 | draft-ffmbkbpadfanegjm | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 전화번호, 연결하기, 연결하기 전화번호, 00, PC원격지원서비스 | 평일, 09, 평일 09, 00, ~ |  |
| 721 | draft-djknghicjnjgdjnj | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 연락처, 부장, 부장 연락처, 성명, 이용진 | Tel, ac, Tel ac, kr, Fax |  |
| 722 | draft-eaiknjdepmgaicba | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 고은영, 기획조정관, 기획조정관 고은영, 개인정보, 보호 | 개인정보, 보호, 개인정보 보호, 분야별, 책임자 |  |
| 723 | draft-oidafcjjfihmbadh | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 대한민국, 마약청정, 마약청정 대한민국, 신청, 안내 | 광역형비자, 시범사업, 광역형비자 시범사업, 참여, 안내 |  |
| 724 | draft-djpjjgnipmdlnifl | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 시행일, 213차, 213차 시행일, 2024-11-12, 개인정보처리방침 | 개인정보처리방침, 212차, 개인정보처리방침 212차, 시행일, 2024-09-09 |  |
| 725 | draft-flnngjfpckfmbmbp | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 불가능, 열람, 열람 불가능, 표현, 4 | 성적증명서, 우편발급, 성적증명서 우편발급, 홈페이지, 에러 |  |
| 726 | draft-imjpbchkkefockkb | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 727 | draft-ojhaedijijchhdab | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 전화, 대표, 대표 전화, 기부자, 예우 | 일, 24, 일 24, 시간, 예약가능 |  |
| 728 | draft-mneohebbbcldcdhm | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2025-12-12 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 729 | draft-ehjegokdodcjjoih | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 1670-0396, 1670-0396 이메일, 직위, 상무 | 개인정보, 고충처리, 개인정보 고충처리, 담당부서, 고객만족센터 |  |
| 730 | draft-pipbkjpopoedijka | EMAIL | EMAIL | enterprise_internal | safe_synthetic_insertion | true_pii | 이메일, 연락, 연락 이메일, 승인, 안내 | 확인, 요청, 확인 요청 |  |
| 731 | draft-oplgmijfkmgomble | EMAIL | EMAIL | general_web | public_web_context | non_pii | 교무팀장, 교무연구처장, 교무연구처장 교무팀장, 8049, 정보지원 | 02, 2204, 02 2204, 8610, 교원 |  |
| 732 | draft-mnaogmmohjnhpani | EMAIL | EMAIL | healthcare | public_web_context | non_pii | e-mail, -, - e-mail, 전화번호, 032 | 제12조, 고정형, 제12조 고정형, 영상정보처리기기, 운영·관리에 |  |
| 733 | draft-nooahoiklacllhhc | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, -, - 이메일, 전화, 팩스 | ①, 정보주체는, ① 정보주체는, 「개인정보, 보호법」 |  |
| 734 | draft-oaibfcjjbpnifepm | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 상담, 채팅, 채팅 상담, 고객센터, 1 | 운영시간, 10, 운영시간 10, 00, ~ |  |
| 735 | draft-fecakafbbkkfiigi | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 곽은영, 당, 당 곽은영, 이메일, 인사총무팀 | ac, kr, ac kr, 개인정보보호, 분임책임자 |  |
| 736 | draft-fhpndjhjbnkcempb | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 화, 전, 전 화, Information, Security | 이메일, email, 이메일 email, protected, 기타 |  |
| 737 | draft-dknoddkgiemdmiba | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 입원계, 원무팀, 원무팀 입원계, 문의, 문의 원무팀 | ~4, 입원, ~4 입원, 안내사항, 병실배정 |  |
| 738 | draft-eiajmfafcboibjpf | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 연락처, 이영은, 이영은 연락처, 개인정보보호, 담당자 | kr, 정보주체께서는, kr 정보주체께서는, 국가민방위재난안전교육원의, 서비스를 |  |
| 739 | draft-okebkimfhbpamahk | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 대한민국, 마약청정, 마약청정 대한민국, 소식을, 알려드립니다 | 올바른, 분리배출, 올바른 분리배출, 안내서, 구미시 |  |
| 740 | draft-dkcnpikokfenakaf | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 126차, 126차 변경일, 2018-02-28, 개인정보처리방침 | 개인정보처리방침, 125차, 개인정보처리방침 125차, 변경일, 2018-01-31 |  |
| 741 | draft-fnompfajgdpnbfcn | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii |  | 시스템, 정기, 시스템 정기, 예방점검, 안내 |  |
| 742 | draft-jgjeolgaiphbpoob | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 743 | draft-ooaaiochpnmnogkk | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | ISMS-KISA-, ISMS, ISMS ISMS-KISA-, 번호, 유효기간 | 11, 04, 11 04, ~, 2026 |  |
| 744 | draft-naebodndfdbfmjmc | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2024-07-29 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 745 | draft-ekafjnjefbgpiblp | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 문의, 대표이사, 대표이사 문의, 소속, 주식회사 | 2, 정보주체는, 2 정보주체는, 회사의, 서비스를 |  |
| 746 | draft-paiabfhkmnbljige | EMAIL | EMAIL | general_web | public_web_context | non_pii | E-mail, 부원장, 부원장 E-mail, 개인정보, 보호책임자 | Fax, 개인정보, Fax 개인정보, 보호담당자, 정보보안팀 |  |
| 747 | draft-namdghdhfjabaphh | EMAIL | EMAIL | healthcare | public_web_context | non_pii | e-mail, 7000, 7000 e-mail, 02, 2276 | 법인명, 서울특별시, 법인명 서울특별시, 서울의료원, 사업자 |  |
| 748 | draft-pgdbffmadodnbgab | EMAIL | EMAIL | public_services | public_web_context | non_pii | 관련문의, 시스템, 시스템 관련문의, 1670-1839, 평일 | 이용약관, 개인정보처리방침, 이용약관 개인정보처리방침, 누리집, 안내지도 |  |
| 749 | draft-oklmbbkogddndomm | PHONE | PHONE_MOBILE | ecommerce | public_web_context | non_pii | -- | 쇼핑몰, 설정, 쇼핑몰 설정, 기본, 내 |  |
| 750 | draft-ffjeancjlgjgmmlf | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 문의, 입학, 입학 문의, 합격확인, 기본등록금납부/확인 | 평일, 09, 평일 09, 00, - |  |
| 751 | draft-fkdidkbjjelokljh | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 전화번호, -, - 전화번호, 개인정보보호, 담당부서 | -, 메, - 메, 일, com |  |
| 752 | draft-dmhkamiopofcgnke | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 연락처, 의무기록팀, 의무기록팀 연락처, 강세리, 소 | 9 |  |
| 753 | draft-ejmaopmanbnpkmmf | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 박상연, 기획협력과, 기획협력과 박상연, 전화, 전자우편 | kr, -, kr -, ①, 정보주체는 |  |
| 754 | draft-pdaldgfoobkfknnf | BANK_ACCOUNT | BANK_ACCOUNT | customer_support | public_web_context | non_pii | 돕기, 이해, 이해 돕기, 2026-01-17, 비자에 | Photo, Gallery, Photo Gallery, 포토갤러리, 필리핀농구대회 |  |
| 755 | draft-dlbnogannkfgokkm | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | ~, 2024-08-19, 2024-08-19 ~, IT, 운영 | 인증번호, IS, 인증번호 IS, 754206, 11 |  |
| 756 | draft-giekgajeppkajaji | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 19, 18, 18 19, 15, 16 | 25, 26, 25 26, 27, 28 |  |
| 757 | draft-jioaflhofhgppimf | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 758 | draft-paejpjlpgpfdfegm | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 휴대폰, 입력, 입력 휴대폰, 이름, 이름 이름 | 019, 휴대폰, 019 휴대폰, 앞자리, - |  |
| 759 | draft-naholljoeoekjjlb | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2025-03-25 |  |
| 760 | draft-eomdenbhiemgjbbf | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 김기남, 보호책임자, 보호책임자 김기남, 통신판매신고번호, 제2007-서울용산-04838 | 사업자정보확인, 고객센터, 사업자정보확인 고객센터, 1670-0396, 월 |  |
| 761 | draft-nepdgpmjaepofafb | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 팩스, 팩스 이메일, 전화, English | 콘텐츠, 관리부서, 콘텐츠 관리부서, 국제진료센터, 상단으로 |  |
| 762 | draft-pgkkcehoclphkacn | EMAIL | EMAIL | public_services | public_web_context | non_pii | 이메일, -, - 이메일, 전화, 팩스 | 제12조, 개인정보, 제12조 개인정보, 열람, 정정·삭제 |  |
| 763 | draft-oklmpkodijhbfgbh | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | TEL, 2022-서울용산-1045, 2022-서울용산-1045 TEL, 사업자등록번호, 사업자정보확인 | FAX, E, FAX E, MAIL, co |  |
| 764 | draft-fhdofgibldbgafbf | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 대표전화, 사업자번호, 사업자번호 대표전화, 이재민, 총장 | ｜, 입시문의, ｜ 입시문의, Copyright, C |  |
| 765 | draft-fpjpdglljpmjdlff | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 통해, 담당자를, 담당자를 통해, 경우, 한국전력공사 | ~, 24, ~ 24, 도움을, 받을 |  |
| 766 | draft-dmlfooghcgbhcgfj | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | ☎ | 레이어, 닫기, 레이어 닫기, 신청자별, 구비서류 |  |
| 767 | draft-emfabeokobdlcjbm | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 13층, 25, 25 13층, 서울특별시, 성동구 | 개인정보, 분쟁조정, 개인정보 분쟁조정, 업무용, 녹취시스템 |  |
| 768 | draft-dlnpkfgmbfgkpebk | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 208차, 208차 변경일, 2024-06-03, 개인정보처리방침 | 개인정보처리방침, 207차, 개인정보처리방침 207차, 변경일, 2024-04-26 |  |
| 769 | draft-gijmbdijnaecifch | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 1990, 1991, 1991 1990, 1994, 1993 | 1984, 1983, 1984 1983, 1982, 1981 |  |
| 770 | draft-jmigigmmkmgdhooe | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 771 | draft-pbnbcpdcmdmblomj | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 휴대전화, 기타, 기타 휴대전화, 내과, 통증클리닉 | 019, -, 019 -, 상담문의, 사이트 |  |
| 772 | draft-ndnekjjcaimiomcf | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2023-05-22 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 773 | draft-fdjdchhfmoelcohb | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 전자우편, /, / 전자우편, 53, 마곡동 | Copyright, C, Copyright C, 2021-2024, WithNature |  |
| 774 | draft-nljnkkhikmbnjhkd | EMAIL | EMAIL | healthcare | public_web_context | non_pii | e-mail, -, - e-mail, 전화번호, 032 | 개인정보보호, 담당자, 개인정보보호 담당자, -, 부서 |  |
| 775 | draft-pjclbmcdcffjghmb | EMAIL | EMAIL | public_services | public_web_context | non_pii | 연락처, 이영은, 이영은 연락처, 개인정보보호, 담당자 | 정보주체께서는, 국가민방위재난안전교육원의, 정보주체께서는 국가민방위재난안전교육원의, 서비스를, 이용하시면서 |  |
| 776 | draft-opildphfdpedkejo | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 전화, –, – 전화, 한국총괄, B2B영업팀 | –, 문의처, – 문의처, keonkyu, com |  |
| 777 | draft-fiemhpgholfcgcon | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii |  | 우, 21041, 우 21041, 인천광역시, 계양구 |  |
| 778 | draft-gbpljnecdcpblphk | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 부장, 권오태, 권오태 부장, 이예진, 주임 | 콘텐츠가치평가시스템, 콘텐츠금융지원팀, 콘텐츠가치평가시스템 콘텐츠금융지원팀, 조재민, 과장 |  |
| 779 | draft-dnoancbjpfanipeb | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 취소, 및, 및 취소, 문의전화, 입원예약 | 병상배정, 확인, 병상배정 확인, 1688-7575, ARS |  |
| 780 | draft-fahcddchkipmoadp | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 김면기, 본인인증, 본인인증 김면기, 책임자, 법무감사담당관 | 개인정보보호정책과장, 잊힐, 개인정보보호정책과장 잊힐, 권리, 김직동 |  |
| 781 | draft-dmeankhmlkhgkkjh | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 확인, 시행방침, 시행방침 확인, 최신, 이전 | -20, 2025-03-19, 2023-08-01, 2023-07-26, 2023-03-14 |  |
| 782 | draft-gndanehmnahdcjnf | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 9, 8, 8 9, 5, 6 | 15, 16, 15 16, 17, 18 |  |
| 783 | draft-jnhgljhgjnfaagpb | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 784 | draft-pefaoinpilliledo | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 사회공헌, 대관안내, 대관안내 사회공헌, 찾아오시는길, 주차안내 | 2020, 2019, 2020 2019, 병원부서, 사회사업팀 |  |
| 785 | draft-nmallpbabidfjjob | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 변경일, 내용, 내용 변경일, 참고정보, -- | 최근, 내용, 최근 내용, 확인일, 2026-02-11 |  |
| 786 | draft-fhaejjlebcocnigd | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 연락처, 연락처 이메일, 팀장, 소속 | 성명, 김상연, 성명 김상연, PL, 소속 |  |
| 787 | draft-oboglnemeemjmdlk | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 책임자, 책임자 이메일, 전화번호, 02 | 진료서비스, 관련, 진료서비스 관련, 개인정보, 관리 |  |
| 788 | draft-pnfmphnjjapidaba | EMAIL | EMAIL | public_services | public_web_context | non_pii | 전자우편, 전화, 전화 전자우편 | 개인정보보호, 담당자, 개인정보보호 담당자, 기획협력과, 이상화 |  |
| 789 | draft-phbfofeoilbhefch | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | 전화번호, 경영지원본부, 경영지원본부 전화번호, 김상연, PL | 이메일, org, 이메일 org, 제10조, org 제10조 |  |
| 790 | draft-fnajiiilnnofjmog | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 대표전화, /, / 대표전화, 포항대학로, 7 | 개인정보보호배상책임보험, II, 개인정보보호배상책임보험 II, 가입, - |  |
| 791 | draft-gigbipchkdjhbhmk | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 없음 | 사업관리시스템, 정보보안팀, 사업관리시스템 정보보안팀, ERP, 전사적자원 |  |
| 792 | draft-dogfjnhdnlehglid | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 입원비확인ARS, 약처방전재발급, 약처방전재발급 입원비확인ARS, 1599-3114, 건강검진예약 | 응급실, 고객상담실, 응급실 고객상담실, 장례식장, 진료의뢰·협력 |  |
| 793 | draft-fdbfamhfbakdmlco | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 주민과, 행정안전부, 행정안전부 주민과, 제도를, 담당하는 | 위, 담당부서와, 위 담당부서와, 전화번호는, 이 |  |
| 794 | draft-dmimhopfcdcakpgd | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 129차, 129차 변경일, 2018-06-01, 개인정보처리방침 | 개인정보처리방침, 128차, 개인정보처리방침 128차, 변경일, 2018-03-13 |  |
| 795 | draft-hgipobjahnkmdhgj | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | ㈜핸디소프트, 유지관리, 유지관리 ㈜핸디소프트, 포함, ○ |  |  |
| 796 | draft-ldgbigmpiebhlhkp | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 797 | draft-peifdbcocddkgnoj | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | +, English, English +, 국제성모병원, 대표번호 | Russian, 응급의료센터, Russian 응급의료센터, 야간, 1600-6119 |  |
| 798 | draft-omijblffcpfaafnh | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2025-03-25 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 799 | draft-fnnefpbcghajadpe | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 1600-0455, 1600-0455 이메일, 개인정보보호책임자, 민혜정 | 온라인디지털콘텐츠산업발전법에, 의한, 온라인디지털콘텐츠산업발전법에 의한, 콘텐츠보호안내, 자세히보기 |  |
| 800 | draft-odboofoijicgmhop | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 책임자, 책임자 이메일, 전화번호, 02 | 진료협력, 개인정보, 진료협력 개인정보, 관리, 부서 |  |
| 801 | draft-piegnfbhleonblka | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | FAX, 022094, 022094 FAX, 2018-경기평택-0099, 부가통신사업신고필증 | 개인정보관리책임자, 김태은, 개인정보관리책임자 김태은, 우인환, 시디즈 |  |
| 802 | draft-fngooapaedgfggeh | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 교육혁신원, 설문조사, 설문조사 교육혁신원, 학부모, 산업체 | 6, 영어특강, 6 영어특강, 프로그램, ㈜한결교육 |  |
| 803 | draft-gkflkenmddeeikdj | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 수출전략팀, 콘텐츠수출마케팅플랫폼, 콘텐츠수출마케팅플랫폼 수출전략팀, 기업부설창작연구소, 한국문화기술기획평가원 | 한국콘텐츠아카데미, 인재양성팀, 한국콘텐츠아카데미 인재양성팀, 콘텐츠도서관, 데이터정책팀 |  |
| 804 | draft-ebbbgbemllmleddc | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 입원비확인ARS, 약처방전재발급, 약처방전재발급 입원비확인ARS, 1599-3114, 건강검진예약 | 응급실, 고객상담실, 응급실 고객상담실, 장례식장, 진료의뢰·협력 |  |
| 805 | draft-fhapcladglnejfbo | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 가름로, 143 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 806 | draft-doadoifmlbbonbnf | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 고객센터, -, - 고객센터, 회원탈퇴, 또는 | 를, 통한, 를 통한, 요청, - |  |
| 807 | draft-himhonchkaedffej | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 문의, 재수강, 재수강 문의, 기간, 만료로 | 수강기간, 완료된, 수강기간 완료된, 강좌, 재신청 |  |
| 808 | draft-ldncomjhfcbhfemo | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 809 | draft-pfehbbklkonjnokl | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | +, Russian, Russian +, 대표번호, 1600-8291 | /2657, 응급의료센터, /2657 응급의료센터, 야간, 1600-6119 |  |
| 810 | draft-oncegjilnkmmdohk | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2026-02-11 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 811 | draft-gaegfbannkfejlcg | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 시까지, 요청, 요청 시까지, 회원, 탈퇴 | Google, LLC, Google LLC, 미국, 1601 |  |
| 812 | draft-odlkmimmecjibfdg | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 책임자, 책임자 이메일, 전화번호, 02 | 후원약정서, 개인정보, 후원약정서 개인정보, 관리, 부서 |  |
| 813 | draft-pkbkdoaifjjaijap | PHONE | PHONE_LANDLINE | ecommerce | public_web_context | non_pii | FAX, 1833-2570, 1833-2570 FAX, 주, 어니스트리 | com, 사업자등록번호, com 사업자등록번호, 사업자번호조회, 통신판매업신고번호 |  |
| 814 | draft-fofgdloemmmddgkb | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 연대장, 예비군연대, 예비군연대 연대장, 센터장, 043 | 취창업지원단, 단장, 취창업지원단 단장, 043, 229-8975 |  |
| 815 | draft-gmpnjbnijncihibo | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 주임, 임나라, 임나라 주임, 과장, 스토리움 | CKL기업지원센터, 기업육성팀, CKL기업지원센터 기업육성팀, 이하영, 차장 |  |
| 816 | draft-eefnlcnoimfalkib | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 대표전화, 연락처, 연락처 대표전화, 20, 서현동 | 응급센터, ⓒ, 응급센터 ⓒ, 2021, DAEJIN |  |
| 817 | draft-flpbnganegkphlcm | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 28, 33길, 33길 28, 서울특별시, 구로구 | 개인정보보호, 현장교육, 개인정보보호 현장교육, 운영, 민원처리 |  |
| 818 | draft-ebkfgkofkbgjnebd | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 시행일, 플라시스템, 플라시스템 시행일, 이용, 개인정보 | /, 제정, / 제정, 2025-09-01, 버전 |  |
| 819 | draft-hjlhnemgjpfdoidj | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | ㈜인핸스유, 시스템, 시스템 ㈜인핸스유, 취업전략팀, ○ |  |  |
| 820 | draft-lhoaajgonchbjmli | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 821 | draft-piiceldadjelpnie | BANK_ACCOUNT | BANK_ACCOUNT | healthcare | public_web_context | non_pii | 선택, 00, 00 선택, 10, ~ | 019, -, 019 -, 신청, 휴대폰 |  |
| 822 | draft-pabfinbaohmpgigb | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2025-12-09 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 823 | draft-geollnhgidfifgmh | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 연락처, 우동효, 우동효 연락처, 직책/직위, 팀장 | 비고, CPO는, 비고 CPO는, 법령이, 정한 |  |
| 824 | draft-oefcjcjileeehgnd | EMAIL | EMAIL | healthcare | public_web_context | non_pii |  | net, Copyright, net Copyright, c, Kyungpook |  |
| 825 | draft-gapllgceppandpgn | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | Tel, 02450, 02450 Tel, 이문로, 107 | /, Fax, / Fax, 대표, 문휘창 |  |
| 826 | draft-goajenecjdcbeejm | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 차장, 이하영, 이하영 차장, 주임, CKL기업지원센터 | 기업부설창작연구소, 한국문화기술기획평가원, 기업부설창작연구소 한국문화기술기획평가원, 경영지원팀, 김학균 |  |
| 827 | draft-efflbbanbeeljgnn | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii |  | 05, 입원치료, 05 입원치료, 중간계산서, 발생시기 |  |
| 828 | draft-fnddajlkpfjijoif | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 엑스, 카카오스토리 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 829 | draft-ecaiopdickgbckne | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 167차, 167차 변경일, 2020-11-28, 개인정보처리방침 | 개인정보처리방침, 166차, 개인정보처리방침 166차, 변경일, 2020-09-29 |  |
| 830 | draft-iapmappdabkagikj | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 입학상담, 입학자료신청, 입학자료신청 입학상담, 입학일정/절차, 상담예약 | 해외전화, 입학상담, 해외전화 입학상담, 1번, 시간제 |  |
| 831 | draft-mliilhggigiihfgg | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 832 | draft-pemandkkcbkcingh | BANK_ACCOUNT | BANK_ACCOUNT | public_services | public_web_context | non_pii | 확인일, 내용, 내용 확인일, 변경일, 2025-12-12 | --, 이, -- 이, 페이지에, 만족하시나요 |  |
| 833 | draft-gfilhaaiefjpdipk | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 일, 메, 메 일, 유료, - | 광고성, 정보, 광고성 정보, 전송, ① |  |
| 834 | draft-pfhnpfcadpglihep | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 응급센터, 대표전화, 대표전화 응급센터, 대표자명, 손경옥 | copyright |  |
| 835 | draft-gbcdoalfkcceeakn | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 서울강서캠퍼스, 입학문의, 입학문의 서울강서캠퍼스, MENU, 학생정보시스템 | 전국, 과정문의, 전국 과정문의, 1588-2282, 예비신입생 |  |
| 836 | draft-hclekpdchhabfkel | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 팩스, 전화, 전화 팩스, 세종사이버대학교, 대표자 | 이메일, ac, 이메일 ac, kr, 등록번호 |  |
| 837 | draft-eipidefjnokpoepa | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 대표전화, 비자신체검사안내, 비자신체검사안내 대표전화, 진료지원부서, 가정간호안내 | 운영시간, 09, 운영시간 09, 00, ~ |  |
| 838 | draft-fpdefgelbkdkilfl | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 엑스, 카카오스토리 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 839 | draft-egpoionpmmkklfaa | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 연락처, 박준태, 박준태 연락처, 소속, 개발F | 이메일, com, 이메일 com, ②, 개인정보 |  |
| 840 | draft-ilmcplpfphpggcmg | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 이메일, 전화번호, 전화번호 이메일, 연락처, 연락처 전화번호 | 019, -, 019 -, 직접입력, 네이버 |  |
| 841 | draft-mokomfhobnagjmnl | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌번호, 환불, 환불 계좌번호, 요청, 요청 환불 | 확인, 승인, 확인 승인 |  |
| 842 | draft-gjjfeafinlfnflag | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 시까지, 요청, 요청 시까지, 회원, 탈퇴 | Google, LLC, Google LLC, 미국, 1601 |  |
| 843 | draft-poghpagihcmgejaa | EMAIL | EMAIL | healthcare | public_web_context | non_pii | 이메일, 책임자, 책임자 이메일, 전화번호, 02 | 채용, 관련, 채용 관련, 개인정보, 관리 |  |
| 844 | draft-geoigalkldpaeiaa | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 교양대학, 프로그램, 프로그램 교양대학, ㈜한결교육, 어학특강 | 7, 도서, 7 도서, 이용자, 관리 |  |
| 845 | draft-hefbljgedponedol | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 콘텐츠IP전략팀, 스토리움, 스토리움 콘텐츠IP전략팀, 이행, 콘텐츠가치평가시스템 | CKL기업지원센터, 기업육성팀, CKL기업지원센터 기업육성팀, 기업부설창작연구소, 한국문화기술기획평가원 |  |
| 846 | draft-ekmjemcbjgickblp | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 건강관리센터, 1600-6119, 1600-6119 건강관리센터, 전화예약, 1600-8291 | ~2, VIP종합건강증진센터, ~2 VIP종합건강증진센터, 특수건강진단, 오시는길 |  |
| 847 | draft-gcjjfbodcgngmenj | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 전화, ·, · 전화, 전문강사, 명단 | ·, 팩스, · 팩스, 이메일, kr |  |
| 848 | draft-ehmifamgdgdkkcjg | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 136차, 136차 변경일, 2018-09-18, 개인정보처리방침 | 개인정보처리방침, 135차, 개인정보처리방침 135차, 변경일, 2018-08-20 |  |
| 849 | draft-jjccgkoeckcphpkd | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 휴대전화, *, * 휴대전화, 이름, 실명 | 019, 이메일, 019 이메일, 우편물, 수령지 |  |
| 850 | draft-mpjnphepjncpphmn | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 851 | draft-gjplkdpeiblfbhfk | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 1833-2570, 1833-2570 이메일, 민원처리, 담당부서 | ※, 자세한, ※ 자세한, 내용은, 아래의 |  |
| 852 | draft-glcnhnlcdeficlcd | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii |  | FAX |  |
| 853 | draft-hjammejncjeaaacn | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 게임기반조성팀, 자격검정, 자격검정 게임기반조성팀, 콘텐츠분쟁조정위원회, 공정상생센터 | ​모바일/VR게임테스트베드, 게임기반조성팀, ​모바일/VR게임테스트베드 게임기반조성팀, 이행, 콘텐츠가치평가 |  |
| 854 | draft-eldpggmlnnafjggp | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | kr, ac, ac kr, 부장, 연락처 | Fax, ②, Fax ②, 정보주체께서는, 가톨릭관동대학교 |  |
| 855 | draft-gfllofngckfenaoc | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | kr, 연락처, 연락처 kr, 신고, 부서명 | ③, 「개인정보, ③ 「개인정보, 보호법」, 제35조 |  |
| 856 | draft-ejgpgaldogafakmk | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 171차, 171차 변경일, 2021-02-26, 개인정보처리방침 | 개인정보처리방침, 170차, 개인정보처리방침 170차, 변경일, 2020-12-21 |  |
| 857 | draft-jojckghmogelbckd | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 1985, 1986, 1986 1985, 1989, 1988 | 1979, 1978, 1979 1978, 1977, 1976 |  |
| 858 | draft-nepkplbcjpgnlkla | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 859 | draft-goepgeebfdiccjap | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 문의, 제휴, 제휴 문의, co, kr | _imgTag_, _imgTag_ _imgTag_, 마이샵, 배송조회, 미확인 |  |
| 860 | draft-gpanmimnlhgkfall | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 안효석, 사무처장, 사무처장 안효석, 스, 이메일 | ac, kr, ac kr, 개인정보보호담당자, 개인정보보호담당자에 |  |
| 861 | draft-iejaepegpfkmgmmj | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | Fax, kr, kr Fax, 유현석, 부원장 | 개인정보, 보호담당자, 개인정보 보호담당자, 정보보안팀, 김인정 |  |
| 862 | draft-enpnjolibchdmdep | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 팩스, 원무과, 원무과 팩스, 영육치료, 대표 | 고신대학교복음병원, 홈페이지는, 고신대학교복음병원 홈페이지는, W3C와, KWCAG |  |
| 863 | draft-ggncpnccnffeflfl | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 전화, ·, · 전화, 이용정보, 본인인증 | ·, 팩스, · 팩스, 이메일, kr |  |
| 864 | draft-emlbifijdemjnajh | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 191차, 191차 변경일, 2022-11-23, 개인정보처리방침 | 개인정보처리방침, 190차, 개인정보처리방침 190차, 변경일, 2022-09-29 |  |
| 865 | draft-kbbglninkimfbold | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 건, 문의의, 문의의 건, 우편발급, 홈페이지 | 기간, 만료로, 기간 만료로, 인한, 재수강 |  |
| 866 | draft-pdgaljmjcdhidjnh | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 867 | draft-hbjdemppjcbbnamm | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, FAX, FAX 이메일, 2016-0099505, TEL | 1, 1문의, 1 1문의, FAQ, 공지사항 |  |
| 868 | draft-hchdmlkjbhiehmca | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 인사총무팀, 통합경비, 통합경비 인사총무팀, 학내, 전체 | 3, 등록금, 3 등록금, 수납, 국민은행 |  |
| 869 | draft-ijaihkiameechnjf | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 전화번호, 연락처, 연락처 전화번호, 부서, 부서명 | 6316, 이메일, 6316 이메일, kr, 닫기 |  |
| 870 | draft-fapheiknblbkemic | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 장례식장, 고객상담실, 고객상담실 장례식장, 약처방전재발급, 입원비확인ARS | ~3, 진료의뢰·협력, ~3 진료의뢰·협력, --, 홈페이지/앱이용문의 |  |
| 871 | draft-gifpoeakppgapfed | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 박다원, 법무감사담당관실, 법무감사담당관실 박다원, 김면기, 개인정보 | ②, 정보주체는, ② 정보주체는, 개인정보위의, 서비스 |  |
| 872 | draft-enajklandgchdpok | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 시행일, 216차, 216차 시행일, 2025-03-28, 적용중 | 개인정보처리방침, 215차, 개인정보처리방침 215차, 시행일, 2024-12-27 |  |
| 873 | draft-kgejcogpdbhgmdjk | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 1970, 1971, 1971 1970, 1974, 1973 | 1964, 년, 1964 년, 선택, 1 |  |
| 874 | draft-pemjdiannmnapebm | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 875 | draft-hgfodgibkdfoaplk | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 1600-0455, 1600-0455 이메일, 개인정보보호책임자, 민혜정 | 온라인디지털콘텐츠산업발전법에, 의한, 온라인디지털콘텐츠산업발전법에 의한, 콘텐츠보호안내, 자세히보기 |  |
| 876 | draft-hgdjjnjgbcjnajgn | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 입시문의, ｜, ｜ 입시문의, 사업자번호, 대표전화 | Copyright, C, Copyright C, Busan, KyungSang |  |
| 877 | draft-ikmhipnanppemknl | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 없음 | 예정, 게임더하기, 예정 게임더하기, 게임유통팀, 홈페이지 |  |
| 878 | draft-fdofhmkbpghffnnc | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 대표전화, 수상동, 수상동 대표전화, 안동시, 앙실로 | 1763, 팩스, 1763 팩스, 06164, 서울특별시 |  |
| 879 | draft-gjefgkpecebdjbkh | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 아동정책팀, 가족복지과, 가족복지과 아동정책팀, 복지부, 상담센터 | 관할, 동, 관할 동, 행정복지센터, 담당자 |  |
| 880 | draft-fbmedihamhcjfmoa | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 151차, 151차 변경일, 2019-07-30, 개인정보처리방침 | 개인정보처리방침, 150차, 개인정보처리방침 150차, 변경일, 2019-07-09 |  |
| 881 | draft-kgggipkheimpbamp | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 2010, 2011, 2011 2010, 2014, 2013 | 2004, 2003, 2004 2003, 2002, 2001 |  |
| 882 | draft-pfnbhekomjgamkob | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 883 | draft-hkfcnjcipdbnbjok | EMAIL | EMAIL | ecommerce | public_web_context | non_pii |  | 미국, 성명, 미국 성명, 성별, 생년월일 |  |
| 884 | draft-hhifglbibdpfapmi | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 첨단범죄수사과, 대검찰청, 대검찰청 첨단범죄수사과, //eprivacy, or | http, //www, http //www, spo, go |  |
| 885 | draft-immdjjbacglljhlo | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 주소, E-mail, E-mail 주소, 개인정보보호담당, TEL | co, kr, co kr, 전라남도, 나주시 |  |
| 886 | draft-fhnkbijcfhmlgngb | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 총무부, 총무과장, 총무과장 총무부, 소속, 연락처 | 접근권한자, 보안팀장, 접근권한자 보안팀장, 주, 신명써비스 |  |
| 887 | draft-gkeldncooekbhokk | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 김면기, 법무감사담당관, 법무감사담당관 김면기, 이정아, 개인정보 | 개인정보, 보호실무담당자, 개인정보 보호실무담당자, 법무감사담당관실, 박다원 |  |
| 888 | draft-fcbmjjbhedbdekkk | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 182차, 182차 변경일, 2022-02-16, 개인정보처리방침 | 개인정보처리방침, 181차, 개인정보처리방침 181차, 변경일, 2021-12-15 |  |
| 889 | draft-klidgkpglnoambda | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 문의, 재수강, 재수강 문의, 기간, 만료로 | RE, 기간, RE 기간, 만료로, 인한 |  |
| 890 | draft-phcacgbahjlkdafb | BANK_ACCOUNT | BANK_ACCOUNT | enterprise_internal | safe_synthetic_insertion | true_pii | 계좌, 환불, 환불 계좌, 승인, 입금 | 처리, 요청, 처리 요청 |  |
| 891 | draft-hkkghlcamjeanjbp | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | PLUS, ALIPAY, ALIPAY PLUS | Tenpay, Payment, Tenpay Payment, Technology, Payment Technology |  |
| 892 | draft-hjlmmoockdcbhabb | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 팩스, 입학처, 입학처 팩스, 이메일무단수집거부, 입학문의 | 58530, 전남, 58530 전남, 무안군, 무안읍 |  |
| 893 | draft-ioogldefccnlkbne | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 사서, 김승호, 김승호 사서, 주임, 콘텐츠도서관 | 게임더하기, 게임산업팀, 게임더하기 게임산업팀, 최그린, 과장 |  |
| 894 | draft-figfehgknjcjncfb | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 진료의뢰·협력, 장례식장, 장례식장 진료의뢰·협력, 입원비확인ARS, 응급실 | --, 홈페이지/앱이용문의, -- 홈페이지/앱이용문의, 오시는, 길 |  |
| 895 | draft-gllpdboiokepnlba | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 주민과, 행정안전부, 행정안전부 주민과, 제도를, 담당하는 | 위, 담당부서와, 위 담당부서와, 전화번호는, 이 |  |
| 896 | draft-fccagcinigbaokhi | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 202차, 202차 변경일, 2023-11-03, 개인정보처리방침 | 개인정보처리방침, 201차, 개인정보처리방침 201차, 변경일, 2023-08-01 |  |
| 897 | draft-kobclnaafkkknlnf | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 해외전화, 1588-2854, 1588-2854 해외전화, 입학자료신청, 입학상담 | -0010, 입학상담, -0010 입학상담, 1번, 시간제 |  |
| 898 | draft-hmgjggagkoabbfal | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 시까지, 요청, 요청 시까지, 종료, 또는 | ※, 국외이전, ※ 국외이전, 거부, 방법·절차 |  |
| 899 | draft-hmdkolccfobgajgj | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 성민DM시스템, 발송, 발송 성민DM시스템, 일자리지원팀, ○ | 2022 |  |
| 900 | draft-jacpdlakpihibgel | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 정보보안팀, 관리시스템, 관리시스템 정보보안팀, ERP, 전사적자원 | 대중문화예술종합정보시스템, 대중음악산업팀, 대중문화예술종합정보시스템 대중음악산업팀, 콘텐츠분쟁조정위원회, 공정상생센터 |  |
| 901 | draft-fiihkdlaikmdcdgl | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | ☎ | 3 |  |
| 902 | draft-gmeembopofogmhdi | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1011호, 에이스한솔타워, 에이스한솔타워 1011호, 가산디지털, 1로 | 개인정보, 영향평가, 개인정보 영향평가, 교육, 및 |  |
| 903 | draft-ffhhkddgmadkimod | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 159차, 159차 변경일, 2020-05-26, 개인정보처리방침 | 개인정보처리방침, 158차, 개인정보처리방침 158차, 변경일, 2020-01-29 |  |
| 904 | draft-koilhlhccljnkocn | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 정보기술, ㈜한국취업, ㈜한국취업 정보기술, 취업통계시스템, 개인정보처리 |  |  |
| 905 | draft-hokccpgjbpcpinjd | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 연락처, 우동효, 우동효 연락처, 부서명, 서비스기획개발팀 | ■, 권익침해, ■ 권익침해, 구제, 방법 |  |
| 906 | draft-icfecdkfgdmdgolj | PHONE | PHONE_MOBILE | education | public_web_context | non_pii | 예 | 3, 개인정보의, 3 개인정보의, 수집, 이용 |  |
| 907 | draft-jbchgfdhfgbgapge | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 인재양성팀, 한국콘텐츠아카데미, 한국콘텐츠아카데미 인재양성팀, 경영지원팀, 콘텐츠수출마케팅플랫폼 | 콘텐츠도서관, 데이터정책팀, 콘텐츠도서관 데이터정책팀, 홈페이지, 유지 |  |
| 908 | draft-fiinemdadonpohcb | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 연락처, 의무부원장, 의무부원장 연락처, 김석연, 소 | 개인정보, 처리, 개인정보 처리, 담당자, 성 |  |
| 909 | draft-hdmbpijcnbclonjg | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 엑스, 카카오스토리 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 910 | draft-fgpjinjmjolpeonl | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 업데이트, 최종, 최종 업데이트 | •, 서비스, • 서비스, 꽃파는총각, 운영 |  |
| 911 | draft-llmenlpgepamdnno | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 선택, 연락처, 연락처 선택, ac, kr | 019, 070, 019 070, -, 자택 |  |
| 912 | draft-holekpmmommkclge | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 전화번호, 전화번호 이메일, 온라인, 화장품 | o, 귀하께서는, o 귀하께서는, 회사의, 서비스를 |  |
| 913 | draft-ihebbnmopgjldbkp | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | FAX, 대표전화, 대표전화 FAX, 고유번호, 총장 | COPYRIGHT, ⓒ, COPYRIGHT ⓒ, SEOUL, CYBER |  |
| 914 | draft-jffkdebkidlcemhd | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 콘텐츠금융지원팀, 시스템, 시스템 콘텐츠금융지원팀, 게임기반조성팀, 이행 | 스토리움, 콘텐츠IP전략팀, 스토리움 콘텐츠IP전략팀, CKL기업지원센터, 기업육성팀 |  |
| 915 | draft-fmnhlbikbkdlnfdp | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 대표전화, 비자신체검사안내, 비자신체검사안내 대표전화, 진료지원부서, 가정간호안내 | 운영시간, 09, 운영시간 09, 00, ~ |  |
| 916 | draft-hhmnjdlaoebmfoca | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 가름로, 143 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 917 | draft-fhcbekecobnkdajh | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 143차, 143차 변경일, 2019-04-02, 개인정보처리방침 | 개인정보처리방침, 142차, 개인정보처리방침 142차, 변경일, 2019-01-01 |  |
| 918 | draft-lmndgeihfblfpnjo | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 메뉴얼, 시험, 시험 메뉴얼, 자가조치방법, 2019-03-19 | 수강료, 환불기준, 수강료 환불기준, 2017-08-30, 반환 |  |
| 919 | draft-hplgakljemcnlgle | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | GYUN, DO, DO GYUN, 개인정보보호, 책임자 | 팩스, _imgTag_, 팩스 _imgTag_, 쿠폰존, n |  |
| 920 | draft-iicfpfjnpkdcipih | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 접수문의사항, 돌아가기, 돌아가기 접수문의사항 |  |  |
| 921 | draft-jjkkgfackkcnobhm | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 재위탁, SAP, SAP 재위탁, 연동, 정보관리책임자 | 이전하는, 개인정보, 이전하는 개인정보, 항목, 성명 |  |
| 922 | draft-fmpgjjmipgifkkch | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 건강검진예약, 1599-3114, 1599-3114 건강검진예약, 예약확인, 진료예약 | 약처방문의, 약처방전재발급, 약처방문의 약처방전재발급, 입원비확인ARS, 응급실 |  |
| 923 | draft-hiohojaddhhcdppd | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 가름로, 143 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 924 | draft-fiemkdaniepcnemi | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 전화, -, - 전화, 담당부서, 유한킴벌리 | -, 이메일, - 이메일, co, kr |  |
| 925 | draft-miahdjabhfppfolm | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii |  | 공지, 2023년, 공지 2023년, 7월, 한국어교원 |  |
| 926 | draft-iceggmjbddkkikma | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 문의, 제휴, 제휴 문의, 공휴일, 제외 | 수출, 제휴, 수출 제휴, 문의, com |  |
| 927 | draft-ioagjmdfglpghhgl | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 팩스, /, / 팩스, 입학관리과, 6001 | COPYRIGHT, C, COPYRIGHT C, MOKPO, NATIONAL |  |
| 928 | draft-jkjajgmmjpmkanlf | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 주임, 이예진, 이예진 주임, 과장, 게임국가기술자격검정 | ​모바일/VR게임테스트베드, 권오태, ​모바일/VR게임테스트베드 권오태, 부장, 콘텐츠가치평가시스템 |  |
| 929 | draft-fogogkchebdnnpge | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 홈페이지/앱이용문의, --, -- 홈페이지/앱이용문의, 고객상담실, 장례식장 | 오시는, 길, 오시는 길, 원내위치안내, -- |  |
| 930 | draft-hknoachfdpkljhbh | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 헬프데스크, 문의, 문의 헬프데스크, 국가재난안전교육원, 시스템 | 평일, 09, 평일 09, 00-18, 00 |  |
| 931 | draft-figcbhdaafmeljbd | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 185차, 185차 변경일, 2022-05-20, 개인정보처리방침 | 개인정보처리방침, 184차, 개인정보처리방침 184차, 변경일, 2022-03-23 |  |
| 932 | draft-mnakmmoggoadhghh | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 2000, 2001, 2001 2000, 2004, 2003 | 1994, 1993, 1994 1993, 1992, 1991 |  |
| 933 | draft-idkccmokfcpffhdh | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 구스타브, 주식회사, 주식회사 구스타브, 2023-고양덕양구-2292, 사업자정보확인 | E-mail, com, E-mail com, 형식으로, 수정해주세요 |  |
| 934 | draft-jamacfdodmldkbdi | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 도너스, 발전기금, 발전기금 도너스, 시, 홍보팀 | 2021 |  |
| 935 | draft-jnanjihlbiedcfee | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 부장, 김정욱, 김정욱 부장, 한국콘텐츠진흥원, 홈페이지 | 사업관리시스템, 김자연, 사업관리시스템 김자연, 주임, ERP |  |
| 936 | draft-geakppeajdcmpkei | PHONE | PHONE_MOBILE | healthcare | public_web_context | non_pii | 연락처, ο, ο 연락처, 담당자, 이종훈 | 개인영상정보의, 확인, 개인영상정보의 확인, 방법, 및 |  |
| 937 | draft-hkpogipadlndijhd | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 전화, -, - 전화, 재난안전교육포탈, 회원정보 | -, 팩스, - 팩스, 이메일, kr |  |
| 938 | draft-fjehhamgnacjffco | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 141차, 141차 변경일, 2019-01-01, 개인정보처리방침 | 개인정보처리방침, 140차, 개인정보처리방침 140차, 변경일, 2018-12-07 |  |
| 939 | draft-mnekoaklailadndh | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii |  | 시스템, 작업, 시스템 작업, 및, 점검 |  |
| 940 | draft-idonahhjhkkfckph | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 메일, /, / 메일, 개인정보관리, 책임자 | COPYRIGHT, ©, COPYRIGHT ©, 2023, 이찌방쿠지 |  |
| 941 | draft-jdekdklpbfejkmfl | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | FAX, 대표전화, 대표전화 FAX, 고유번호, 총장 | COPYRIGHT, ⓒ, COPYRIGHT ⓒ, SEOUL, CYBER |  |
| 942 | draft-joejmoalbbgoieja | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 부장, 허강, 허강 부장, 주임, ERP | 대중문화예술종합정보시스템, 대중음악산업팀, 대중문화예술종합정보시스템 대중음악산업팀, 정철우, 과장 |  |
| 943 | draft-gfhkbnkpealpjgef | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 문의, 안함, 안함 문의, 휴진, 시 | --, 단, -- 단, 보험사, 직원이 |  |
| 944 | draft-hodoelmkmgljfndj | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 팩스, ·, · 팩스, 나상철, 전화 | ·, 이메일, · 이메일, kr, 데이터안전 |  |
| 945 | draft-flkjccclgenkodbm | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 163차, 163차 변경일, 2020-09-01, 개인정보처리방침 | 개인정보처리방침, 162차, 개인정보처리방침 162차, 변경일, 2020-07-01 |  |
| 946 | draft-ncngjehdcknheinn | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 14, 13, 13 14, 10, 11 | 20, 21, 20 21, 22, 23 |  |
| 947 | draft-iimkomlplbfggljl | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | ●, 유료, 유료 ●, 국번없이, 1599-0110 | ※, 세부, ※ 세부, 내용은, 개인정보처리방침 |  |
| 948 | draft-jeipldfonjlomjpj | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii |  | 패밀리, 사이트, 패밀리 사이트, 덕성여자대학교, 전면 |  |
| 949 | draft-kakikmolfgfggfak | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 전화번호, 연락처, 연락처 전화번호, 부서명, 정보보안팀 | 6316, 이메일, 6316 이메일, kr, 콘텐츠 |  |
| 950 | draft-gfpcdgmklbimfhik | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | Us, Contact, Contact Us | 배너존, 이전보기, 배너존 이전보기, 정지, 이전보기 배너존 |  |
| 951 | draft-ibiigoonnobconpc | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 엑스, 카카오스토리 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 952 | draft-flpaegcnhmlfcmpb | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | +, 해외주문, 해외주문 +, 30, 365 | --, -- --, AI, 화환, 주문 |  |
| 953 | draft-nokcgdlpbdlplhpm | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | ㈜아이엠지테크, 연구실안전관리시스템, 연구실안전관리시스템 ㈜아이엠지테크, 대학원, 포함 |  |  |
| 954 | draft-iknhlleailnnbahd | EMAIL | EMAIL | ecommerce | public_web_context | non_pii |  | 개인정보가, 이전되는, 개인정보가 이전되는, 국가, 싱가포르 |  |
| 955 | draft-jfmmnepacghleond | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 전화번호, 원, 원 전화번호, 성명, 장 | 이메일, ac, 이메일 ac, kr, 개인정보 |  |
| 956 | draft-kdplidgedcabadop | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 과장, 선지혜, 선지혜 과장, 콘텐츠분쟁조정위원회, 공정상생센터 | 게임국가기술자격검정, 게임기반조성팀, 게임국가기술자격검정 게임기반조성팀, 이예진, 주임 |  |
| 957 | draft-ggpldfodgbjemdgm | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 대표전화, 28, 28 대표전화, 대학로, 101 | 예약센터, 1588-5700, 예약센터 1588-5700, --, 대표전화 |  |
| 958 | draft-icdfleolkbhjghmo | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 팩스, 전화, 전화 팩스 | 전자우편, kr, 전자우편 kr, 개인정보보호, 담당자 |  |
| 959 | draft-fmdnnkdeafopogcj | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 시행일, 212차, 212차 시행일, 2024-10-14, 개인정보처리방침 | 개인정보처리방침, 211차, 개인정보처리방침 211차, 시행일, 2024-08-14 |  |
| 960 | draft-npbjemeogfjgaglh | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii |  | 공지, 시스템, 공지 시스템, 인프라, 점검 |  |
| 961 | draft-imdbamdlljnmbnop | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 1566-0406, 1566-0406 이메일, 부서, CS부서 | o, 개인정보, o 개인정보, 보호담당자, 성명 |  |
| 962 | draft-jhkgehokknncmnjn | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 학술정보팀, 유지관리, 유지관리 학술정보팀, 이용자, 정보 | 8, 홈페이지, 8 홈페이지, 운영, ㈜한신정보기술 |  |
| 963 | draft-keoggceldlhgifjj | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 전화, 부장, 부장 전화, 처장, 성명 | 전화, 팩스, 전화 팩스, 주소, 전라남도 |  |
| 964 | draft-gopmeepjkakeknjg | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | ☎ | 온라인, 사본발급, 온라인 사본발급, 신청, 사본발급 신청 |  |
| 965 | draft-iefcgaloemenalep | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 가름로, 143 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 966 | draft-fpekejapccbgbcea | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 197차, 197차 변경일, 2023-05-10, 개인정보처리방침 | 개인정보처리방침, 196차, 개인정보처리방침 196차, 변경일, 2023-03-22 |  |
| 967 | draft-obdmheploofdhkjf | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | *, 휴대전화, 휴대전화 *, 50대, 60대 | 019, 070, 019 070, -, 이메일 |  |
| 968 | draft-inelbcfapkelhcah | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 1670-0396, 1670-0396 이메일, 담당부서, 고객만족센터 | 제10조, 권익침해, 제10조 권익침해, 구제방법, 이용자는 |  |
| 969 | draft-jhldlpodiflajkab | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 대표전화, 이은주, 이은주 대표전화, 제2014-서울강북-0056, 고유번호 | FAX, COPYRIGHT, FAX COPYRIGHT, ⓒ, SEOUL |  |
| 970 | draft-kgplnajnmgmljnfa | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii |  | ©, LS, © LS, Cable, & |  |
| 971 | draft-hbddmedfkcmhfgca | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 대표전화, 비자신체검사안내, 비자신체검사안내 대표전화, 진료지원부서, 가정간호안내 | 운영시간, 09, 운영시간 09, 00, ~ |  |
| 972 | draft-ieoflofdbcbnimbd | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 팩스, ·, · 팩스, 박다원, 전화 | ·, 이메일, · 이메일, kr, ② |  |
| 973 | draft-gdegloomhmcljool | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 198차, 198차 변경일, 2023-06-02, 개인정보처리방침 | 개인정보처리방침, 197차, 개인정보처리방침 197차, 변경일, 2023-04-14 |  |
| 974 | draft-odppdnjdakmdnfag | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 불가능, 열람, 열람 불가능, 표현, 4 | RE, 애니메이션으로, RE 애니메이션으로, 배우는, 중국어 |  |
| 975 | draft-ineoiiehijfamgbg | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, /, / 이메일, 통신판매업신고번호, 제 | 개인정보취급방침, 이용약관, 개인정보취급방침 이용약관, ©, 2023 |  |
| 976 | draft-jkliihipfljdbggp | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | 정보보호마크인증위원회, kr, kr 정보보호마크인증위원회, //www, kopico | ~4, http, ~4 http, //eprivacy, or |  |
| 977 | draft-kjaokbokaeigiofk | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | 정보보안팀, 홈페이지, 홈페이지 정보보안팀, 수탁사, 교육·점검 | 홈페이지, 유지, 홈페이지 유지, 관리, 웹사이트 |  |
| 978 | draft-hdhdomffmhoampeh | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | ☎ | Q, 출력이, Q 출력이, 안, 되었는데 |  |
| 979 | draft-ihiglfaoglppilcg | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 전화, 연락처, 연락처 전화, 담당자, 이혜림 | 이메일, kr, 이메일 kr, 팩스, ③ |  |
| 980 | draft-gdglllgblokonenh | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 전화, 전화 전화, 부서명, 유한킴벌리, 고객지원센터 | 이메일, co, 이메일 co, kr, co kr |  |
| 981 | draft-oepiajkkilbebjlf | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 입학상담, 입학자료신청, 입학자료신청 입학상담, 입학일정/절차, 상담예약 | 해외전화, 입학상담, 해외전화 입학상담, 1번, 시간제 |  |
| 982 | draft-ipgchiejfcedgcgj | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 고객센터, 고객센터 이메일, 토요일, 9시~12시 | 10 |  |
| 983 | draft-jlhmngghdlmiokle | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | FAX, 1588-2854, 1588-2854 FAX, 460, 원광디지털대학교 | 사업자등록번호, 대표, 사업자등록번호 대표, 김윤철, Copyright |  |
| 984 | draft-klcapklbahbkilch | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii |  | 6316, Fax, 6316 Fax |  |
| 985 | draft-hfnmipghkpcnpcff | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 연락처, 부산대학교병원, 부산대학교병원 연락처, 담당부서, 담당부서 부산대학교병원 | 오류신고하기, --, 오류신고하기 --, PNUH, 네트워크 |  |
| 986 | draft-indhlghinlohlodh | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 전화, ·, · 전화, 분쟁조정, 신청정보 | ·, 팩스, · 팩스, 이메일, kr |  |
| 987 | draft-gffccbilnjgogflm | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 시행일, 210차, 210차 시행일, 2024-08-14, 개인정보처리방침 | 개인정보처리방침, 209차, 개인정보처리방침 209차, 변경일, 2024-06-03 |  |
| 988 | draft-pdkibgfkcgabjjme | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii | 재신청, 강좌, 강좌 재신청, 2026-03-26, 수강기간 | RE, 수강기간, RE 수강기간, 완료된, 강좌 |  |
| 989 | draft-jbighekhailafbij | EMAIL | EMAIL | ecommerce | public_web_context | non_pii | 이메일, 1670-0396, 1670-0396 이메일, 담당부서, 고객만족센터 | 제10조, 권익침해, 제10조 권익침해, 구제방법, 이용자는 |  |
| 990 | draft-jmchmnfappbnedfm | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | Tel, 입학·홍보팀, 입학·홍보팀 Tel, 가정북로, 68 | 0212, /, 0212 /, Fax, 사업자등록번호 |  |
| 991 | draft-kpgckbnfcdcbmmkc | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii |  | 6314, kr, 6314 kr, 여기가, 고충처리부서인 |  |
| 992 | draft-higjghppjdlcegmo | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii | 고객상담실, 응급실, 응급실 고객상담실, 약처방문의, 약처방전재발급 | 장례식장, 진료의뢰·협력, 장례식장 진료의뢰·협력, --, 홈페이지/앱이용문의 |  |
| 993 | draft-inhnjndimpbckkie | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 가름로, 143 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
| 994 | draft-ghaidmfoiobgoeln | BANK_ACCOUNT | BANK_ACCOUNT | ecommerce | public_web_context | non_pii | 변경일, 135차, 135차 변경일, 2018-09-01, 개인정보처리방침 | 개인정보처리방침, 134차, 개인정보처리방침 134차, 변경일, 2018-08-08 |  |
| 995 | draft-peknjellmogmmnmp | BANK_ACCOUNT | BANK_ACCOUNT | education | public_web_context | non_pii |  | 공지, Q&A, 공지 Q&A, 공지사항, 안내 |  |
| 996 | draft-jfhccldjbejkgbnl | EMAIL | EMAIL | ecommerce | public_web_context | non_pii |  | /, 미국, / 미국, 성명, 성별 |  |
| 997 | draft-kbbdpfglcdhpeghm | PHONE | PHONE_LANDLINE | education | public_web_context | non_pii | TEL, 5, 5 TEL, 분당구, 황새울로 | 한국폴리텍대학, 보이는, 한국폴리텍대학 보이는, ARS, 이용은 |  |
| 998 | draft-lbembmhioaifkhhj | PHONE | PHONE_LANDLINE | general_web | public_web_context | non_pii | kr, ac, ac kr, 대학원장, 대학원교학팀 | 대학원, 입시, 대학원 입시, 학적관리, 학사관리 |  |
| 999 | draft-hijgeimjpojpkhck | PHONE | PHONE_LANDLINE | healthcare | public_web_context | non_pii |  | 병리과, 슬라이드, 병리과 슬라이드, 대출, 발급비용 |  |
| 1000 | draft-inpahkgnpigiiiid | PHONE | PHONE_LANDLINE | public_services | public_web_context | non_pii | 1588-2188, 콜센터, 콜센터 1588-2188, 엑스, 카카오스토리 | 지역번호, 02, 지역번호 02, 를, 확인하세요 |  |
