# M4 Data.go.kr Download Status v1

- generated_at: 2026-06-05T17:29:12+09:00
- raw_root: C:\Users\andyw\Desktop\M4_raw_staging\data_go_kr
- repository_safety: raw files are outside repository; no service key or raw record values are stored here.
- file_count_total: 779
- compressed_or_raw_bytes_total: 1878014891

## Dataset Status

| dataset | status | records | local files | bytes | M4 role | note |
|---|---|---:|---:|---:|---|---|
| fair_trade_online_sales | downloaded_csv_and_api_detail | CSV rows about 2.29M; API totalCount 2,623,221 | 283 | 1187961897 | public-record representative, business ID, phone/email/address, domain and operating-status context | Regional FTC CSV files and full MllBsDtl_3Service detail API pages were downloaded. |
| fair_trade_door_to_door_sales | downloaded_csv | 16 regional CSV files | 17 | 6021513 | public-record representative, corporate/business ID, phone/email/address context | Regional FTC CSV files were downloaded. |
| commercial_store_info | downloaded_zip | 1 data.go.kr ZIP | 2 | 341022592 | shop names, organization/public address and phone context, shop-name false-positive context | The user-provided Downloads copy matches the staged ZIP by size/hash prefix checked earlier. |
| hira_hospital_info | downloaded_api_and_filedata_fallbacks | HIRA API totalCount 79,703 plus 6 CSV fallbacks | 22 | 9541977 | hospital/clinic/public health organization names, public address and phone context | Full getHospBasisList API pages were downloaded after approved key was provided. |
| financial_company_basic_info | downloaded_api | API totalCount 2,219,487 | 223 | 250028374 | financial-company representative, corporate registration, address, phone context | Full getFnCoOutl API pages were downloaded. |
| corporate_basic_info | downloaded_api | API totalCount 1,272,078 | 129 | 83311176 | corporate representative, business/corporate registration, address, phone context | Full getCorpOutline_V2 API pages were downloaded. |
| nts_business_status | initial_batch_downloaded | 10,000 of 2,202,103 discovered unique business numbers | 100 | 122852 | business-registration status validation evidence for public business identifier context | Full status enrichment is possible with --max-business-numbers 0, but initial proof batch was used to avoid turning validation into the bottleneck. |
| pps_nara_marketplace | blocked_provider_application_error | catalog metadata only | 1 | 1442 | procurement supplier/company context pending provider API resolution | data.go.kr gateway returned 404; nopenapi.g2b operation URL returned provider application error under tested conditions. |
| road_name_address | metadata_only_search_api_key_required | catalog metadata only | 1 | 1534 | road-name address structure pending juso approval key/DB download | This source is a search API, not a bulk DB dump. |
| detailed_address | blocked_institution_download_or_browser_required | catalog metadata only | 1 | 1534 | dong/floor/ho detailed-address structure pending juso DB download | data.go.kr points to juso institution download; direct shell access returned 404/timeout and Codex Chrome connection failed. |

## Operation Inventory

| operation | files | bytes |
|---|---:|---:|
| commercial_store_info | 2 | 341022592 |
| corporate_basic_info | 1 | 1985 |
| corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | 128 | 83309191 |
| detailed_address | 1 | 1534 |
| fair_trade_door_to_door_sales | 17 | 6021513 |
| fair_trade_online_sales | 20 | 912271585 |
| fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | 263 | 275690312 |
| financial_company_basic_info | 1 | 2165 |
| financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | 222 | 250026209 |
| hira_hospital_info | 14 | 2702326 |
| hira_hospital_info/api_hospInfoServicev2_getHospBasisList | 8 | 6839651 |
| nts_business_status/api_nts_businessman_status | 100 | 122852 |
| pps_nara_marketplace | 1 | 1442 |
| road_name_address | 1 | 1534 |

## File Inventory

| dataset | operation | file | bytes |
|---|---|---|---:|
| commercial_store_info | commercial_store_info | commercial_store_info/data_go_kr_catalog_15083033_fileData.json | 1591 |
| commercial_store_info | commercial_store_info | commercial_store_info/small_business_store_info_20260331.zip | 341021001 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00001.json.gz | 545798 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00002.json.gz | 574511 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00003.json.gz | 584445 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00004.json.gz | 579418 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00005.json.gz | 627129 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00006.json.gz | 597528 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00007.json.gz | 612632 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00008.json.gz | 635736 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00009.json.gz | 659183 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00010.json.gz | 668361 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00011.json.gz | 664628 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00012.json.gz | 689401 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00013.json.gz | 694843 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00014.json.gz | 701041 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00015.json.gz | 716713 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00016.json.gz | 729849 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00017.json.gz | 726723 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00018.json.gz | 729568 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00019.json.gz | 730878 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00020.json.gz | 731923 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00021.json.gz | 737981 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00022.json.gz | 742786 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00023.json.gz | 741191 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00024.json.gz | 742355 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00025.json.gz | 749596 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00026.json.gz | 740935 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00027.json.gz | 736045 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00028.json.gz | 744001 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00029.json.gz | 735659 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00030.json.gz | 735148 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00031.json.gz | 722455 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00032.json.gz | 718076 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00033.json.gz | 713085 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00034.json.gz | 716990 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00035.json.gz | 711235 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00036.json.gz | 711911 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00037.json.gz | 702723 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00038.json.gz | 705340 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00039.json.gz | 702082 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00040.json.gz | 707902 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00041.json.gz | 704274 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00042.json.gz | 657627 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00043.json.gz | 648842 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00044.json.gz | 663782 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00045.json.gz | 613409 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00046.json.gz | 664717 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00047.json.gz | 640133 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00048.json.gz | 574276 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00049.json.gz | 625830 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00050.json.gz | 687569 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00051.json.gz | 702283 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00052.json.gz | 703309 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00053.json.gz | 692740 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00054.json.gz | 664582 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00055.json.gz | 695391 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00056.json.gz | 610134 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00057.json.gz | 657127 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00058.json.gz | 618675 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00059.json.gz | 709556 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00060.json.gz | 702930 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00061.json.gz | 659856 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00062.json.gz | 682780 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00063.json.gz | 687671 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00064.json.gz | 645338 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00065.json.gz | 697115 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00066.json.gz | 657899 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00067.json.gz | 634453 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00068.json.gz | 650414 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00069.json.gz | 702041 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00070.json.gz | 636604 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00071.json.gz | 654679 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00072.json.gz | 679361 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00073.json.gz | 669799 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00074.json.gz | 628839 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00075.json.gz | 659570 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00076.json.gz | 660512 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00077.json.gz | 634399 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00078.json.gz | 693984 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00079.json.gz | 653799 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00080.json.gz | 588070 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00081.json.gz | 585365 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00082.json.gz | 644766 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00083.json.gz | 599428 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00084.json.gz | 575500 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00085.json.gz | 655138 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00086.json.gz | 635840 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00087.json.gz | 613958 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00088.json.gz | 661550 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00089.json.gz | 625210 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00090.json.gz | 629707 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00091.json.gz | 555825 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00092.json.gz | 626495 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00093.json.gz | 643618 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00094.json.gz | 625310 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00095.json.gz | 597993 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00096.json.gz | 566265 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00097.json.gz | 589017 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00098.json.gz | 600973 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00099.json.gz | 532529 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00100.json.gz | 607789 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00101.json.gz | 661726 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00102.json.gz | 671005 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00103.json.gz | 667337 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00104.json.gz | 675300 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00105.json.gz | 643218 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00106.json.gz | 551199 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00107.json.gz | 595742 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00108.json.gz | 638665 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00109.json.gz | 586920 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00110.json.gz | 603330 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00111.json.gz | 572837 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00112.json.gz | 644155 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00113.json.gz | 644908 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00114.json.gz | 620021 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00115.json.gz | 584534 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00116.json.gz | 578450 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00117.json.gz | 589749 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00118.json.gz | 552209 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00119.json.gz | 553479 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00120.json.gz | 600895 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00121.json.gz | 625104 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00122.json.gz | 624067 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00123.json.gz | 673282 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00124.json.gz | 665584 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00125.json.gz | 651074 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00126.json.gz | 680733 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00127.json.gz | 676949 |
| corporate_basic_info | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2 | corporate_basic_info/api_GetCorpBasicInfoService_V2_getCorpOutline_V2/page_00128.json.gz | 172270 |
| corporate_basic_info | corporate_basic_info | corporate_basic_info/data_go_kr_catalog_15043184_openapi.json | 1985 |
| detailed_address | detailed_address | detailed_address/data_go_kr_catalog_15050425_fileData.json | 1534 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/data_go_kr_catalog_15083259_fileData.json | 1697 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_강원특별자치도 전체.csv | 185307 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_경기도 전체.csv | 999257 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_경상남도 전체.csv | 235892 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_경상북도 전체.csv | 251398 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_광주광역시 전체.csv | 209432 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_대구광역시 전체.csv | 316228 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_대전광역시 전체.csv | 269468 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_부산광역시 전체.csv | 467783 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_서울특별시 전체.csv | 1838219 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_울산광역시 전체.csv | 123449 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_인천광역시 전체.csv | 334420 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_전라남도 전체.csv | 175228 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_전북특별자치도 전체.csv | 145537 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_제주특별자치도 전체.csv | 57677 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_충청남도 전체.csv | 221036 |
| fair_trade_door_to_door_sales | fair_trade_door_to_door_sales | fair_trade_door_to_door_sales/방문판매사업자_ALL_충청북도 전체.csv | 189485 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00001.json.gz | 947685 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00002.json.gz | 925434 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00003.json.gz | 1026581 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00004.json.gz | 1043325 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00005.json.gz | 1013060 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00006.json.gz | 974391 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00007.json.gz | 983185 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00008.json.gz | 1000459 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00009.json.gz | 934587 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00010.json.gz | 845751 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00011.json.gz | 956534 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00012.json.gz | 1016156 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00013.json.gz | 1002848 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00014.json.gz | 951575 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00015.json.gz | 981344 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00016.json.gz | 967191 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00017.json.gz | 1034897 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00018.json.gz | 851991 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00019.json.gz | 841044 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00020.json.gz | 999089 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00021.json.gz | 1000795 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00022.json.gz | 976023 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00023.json.gz | 965620 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00024.json.gz | 970600 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00025.json.gz | 1018400 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00026.json.gz | 886625 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00027.json.gz | 811442 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00028.json.gz | 950750 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00029.json.gz | 1003521 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00030.json.gz | 1008499 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00031.json.gz | 967367 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00032.json.gz | 965995 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00033.json.gz | 964380 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00034.json.gz | 1060573 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00035.json.gz | 770600 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00036.json.gz | 876113 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00037.json.gz | 992774 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00038.json.gz | 995236 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00039.json.gz | 953863 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00040.json.gz | 969035 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00041.json.gz | 953942 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00042.json.gz | 1046771 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00043.json.gz | 800782 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00044.json.gz | 923507 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00045.json.gz | 1003856 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00046.json.gz | 985824 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00047.json.gz | 973974 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00048.json.gz | 953939 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00049.json.gz | 947534 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00050.json.gz | 1047432 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00051.json.gz | 775771 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00052.json.gz | 871822 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00053.json.gz | 989898 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00054.json.gz | 976474 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00055.json.gz | 973664 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00056.json.gz | 968985 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00057.json.gz | 957021 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00058.json.gz | 989471 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00059.json.gz | 957367 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00060.json.gz | 803124 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00061.json.gz | 960565 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00062.json.gz | 982066 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00063.json.gz | 987595 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00064.json.gz | 965044 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00065.json.gz | 965964 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00066.json.gz | 1006609 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00067.json.gz | 903333 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00068.json.gz | 816685 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00069.json.gz | 962580 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00070.json.gz | 993669 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00071.json.gz | 1001554 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00072.json.gz | 975816 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00073.json.gz | 964602 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00074.json.gz | 974459 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00075.json.gz | 949443 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00076.json.gz | 819202 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00077.json.gz | 972292 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00078.json.gz | 987465 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00079.json.gz | 981828 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00080.json.gz | 966744 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00081.json.gz | 950448 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00082.json.gz | 985254 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00083.json.gz | 961082 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00084.json.gz | 812441 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00085.json.gz | 925017 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00086.json.gz | 978747 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00087.json.gz | 994360 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00088.json.gz | 967108 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00089.json.gz | 953069 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00090.json.gz | 973839 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00091.json.gz | 1045905 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00092.json.gz | 775081 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00093.json.gz | 872570 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00094.json.gz | 994103 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00095.json.gz | 986142 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00096.json.gz | 970955 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00097.json.gz | 950081 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00098.json.gz | 959489 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00099.json.gz | 1024428 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00100.json.gz | 885523 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00101.json.gz | 819653 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00102.json.gz | 938441 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00103.json.gz | 985057 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00104.json.gz | 992918 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00105.json.gz | 948258 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00106.json.gz | 932269 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00107.json.gz | 995462 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00108.json.gz | 984099 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00109.json.gz | 820085 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00110.json.gz | 930429 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00111.json.gz | 986306 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00112.json.gz | 986140 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00113.json.gz | 948266 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00114.json.gz | 949419 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00115.json.gz | 962055 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00116.json.gz | 1039758 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00117.json.gz | 819290 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00118.json.gz | 873487 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00119.json.gz | 995315 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00120.json.gz | 943435 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00121.json.gz | 945410 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00122.json.gz | 951745 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00123.json.gz | 942640 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00124.json.gz | 1042585 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00125.json.gz | 829202 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00126.json.gz | 862652 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00127.json.gz | 989269 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00128.json.gz | 989014 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00129.json.gz | 934871 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00130.json.gz | 925595 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00131.json.gz | 986124 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00132.json.gz | 1033798 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00133.json.gz | 1036954 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00134.json.gz | 977533 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00135.json.gz | 939350 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00136.json.gz | 976900 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00137.json.gz | 967552 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00138.json.gz | 993369 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00139.json.gz | 792352 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00140.json.gz | 909582 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00141.json.gz | 799450 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00142.json.gz | 795739 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00143.json.gz | 991312 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00144.json.gz | 995903 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00145.json.gz | 912985 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00146.json.gz | 975253 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00147.json.gz | 955938 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00148.json.gz | 1003924 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00149.json.gz | 1048169 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00150.json.gz | 819751 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00151.json.gz | 967489 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00152.json.gz | 980953 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00153.json.gz | 943507 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00154.json.gz | 939235 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00155.json.gz | 931614 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00156.json.gz | 993259 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00157.json.gz | 998644 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00158.json.gz | 825262 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00159.json.gz | 968112 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00160.json.gz | 1009609 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00161.json.gz | 963988 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00162.json.gz | 931262 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00163.json.gz | 956293 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00164.json.gz | 969928 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00165.json.gz | 1037018 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00166.json.gz | 823628 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00167.json.gz | 939621 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00168.json.gz | 1005816 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00169.json.gz | 962192 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00170.json.gz | 925015 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00171.json.gz | 960815 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00172.json.gz | 935641 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00173.json.gz | 1052234 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00174.json.gz | 1041407 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00175.json.gz | 1055300 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00176.json.gz | 1010082 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00177.json.gz | 977185 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00178.json.gz | 941626 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00179.json.gz | 950422 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00180.json.gz | 962376 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00181.json.gz | 1050021 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00182.json.gz | 1198920 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00183.json.gz | 1204981 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00184.json.gz | 1198551 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00185.json.gz | 1158842 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00186.json.gz | 1177819 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00187.json.gz | 1113015 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00188.json.gz | 1060254 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00189.json.gz | 1360673 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00190.json.gz | 1348979 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00191.json.gz | 1272515 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00192.json.gz | 1227077 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00193.json.gz | 1151189 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00194.json.gz | 1177781 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00195.json.gz | 1375535 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00196.json.gz | 1306251 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00197.json.gz | 1268405 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00198.json.gz | 1255938 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00199.json.gz | 1119563 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00200.json.gz | 1137306 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00201.json.gz | 1182110 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00202.json.gz | 1154600 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00203.json.gz | 1125212 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00204.json.gz | 1141640 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00205.json.gz | 1073026 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00206.json.gz | 1125901 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00207.json.gz | 1133394 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00208.json.gz | 1042384 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00209.json.gz | 1108116 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00210.json.gz | 1070936 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00211.json.gz | 1035117 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00212.json.gz | 1029657 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00213.json.gz | 1054350 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00214.json.gz | 1225761 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00215.json.gz | 1306306 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00216.json.gz | 1303020 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00217.json.gz | 1310296 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00218.json.gz | 1308259 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00219.json.gz | 1291381 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00220.json.gz | 1324046 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00221.json.gz | 1316025 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00222.json.gz | 1329218 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00223.json.gz | 1302625 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00224.json.gz | 1321239 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00225.json.gz | 1308670 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00226.json.gz | 1290180 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00227.json.gz | 1320633 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00228.json.gz | 1313661 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00229.json.gz | 915908 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00230.json.gz | 828829 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00231.json.gz | 1109405 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00232.json.gz | 1260581 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00233.json.gz | 1269586 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00234.json.gz | 1314058 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00235.json.gz | 1278746 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00236.json.gz | 1286823 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00237.json.gz | 1284684 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00238.json.gz | 1319623 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00239.json.gz | 1369470 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00240.json.gz | 1389460 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00241.json.gz | 1369693 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00242.json.gz | 1348390 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00243.json.gz | 1390667 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00244.json.gz | 1372253 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00245.json.gz | 1314185 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00246.json.gz | 1304012 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00247.json.gz | 1342856 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00248.json.gz | 1391697 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00249.json.gz | 1421980 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00250.json.gz | 1443566 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00251.json.gz | 1406977 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00252.json.gz | 1426397 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00253.json.gz | 1445839 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00254.json.gz | 1443047 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00255.json.gz | 1437532 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00256.json.gz | 1303675 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00257.json.gz | 1449964 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00258.json.gz | 1440405 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00259.json.gz | 1525933 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00260.json.gz | 1494817 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00261.json.gz | 1515210 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00262.json.gz | 1461396 |
| fair_trade_online_sales | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3 | fair_trade_online_sales/api_MllBsDtl_3Service_getMllBsInfoDetail_3/page_00263.json.gz | 457021 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/data_go_kr_catalog_15083251_fileData.json | 2015 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/data_go_kr_catalog_15126315_openapi.json | 926 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_강원특별자치도 전체.csv | 20392705 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_경기도 전체.csv | 288613967 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_경상남도 전체.csv | 33370937 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_경상북도 전체.csv | 28535472 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_광주광역시 전체.csv | 16977067 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_대구광역시 전체.csv | 36973004 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_대전광역시 전체.csv | 22425579 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_부산광역시 전체.csv | 47304449 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_서울특별시 전체.csv | 258154717 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_세종특별자치시 전체.csv | 4483442 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_울산광역시 전체.csv | 9412570 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_인천광역시 전체.csv | 58612115 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_전라남도 전체.csv | 16573575 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_전북특별자치도 전체.csv | 16810999 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_제주특별자치도 전체.csv | 11999311 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_충청남도 전체.csv | 24866916 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_ALL_충청북도 전체.csv | 16748507 |
| fair_trade_online_sales | fair_trade_online_sales | fair_trade_online_sales/통신판매사업자_국외사업자.csv | 13312 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00001.json.gz | 1131323 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00002.json.gz | 1131012 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00003.json.gz | 1133092 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00004.json.gz | 1132574 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00005.json.gz | 1133215 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00006.json.gz | 1131304 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00007.json.gz | 1132476 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00008.json.gz | 1132080 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00009.json.gz | 1133798 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00010.json.gz | 1132964 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00011.json.gz | 1132603 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00012.json.gz | 1132985 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00013.json.gz | 1133210 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00014.json.gz | 1134637 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00015.json.gz | 1118349 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00016.json.gz | 837073 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00017.json.gz | 1033407 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00018.json.gz | 1134113 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00019.json.gz | 1133942 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00020.json.gz | 1134062 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00021.json.gz | 1132331 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00022.json.gz | 1133109 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00023.json.gz | 1134110 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00024.json.gz | 1133707 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00025.json.gz | 1131300 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00026.json.gz | 1131854 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00027.json.gz | 1132757 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00028.json.gz | 1130712 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00029.json.gz | 1132696 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00030.json.gz | 1133728 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00031.json.gz | 1131393 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00032.json.gz | 1132496 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00033.json.gz | 1130266 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00034.json.gz | 1131127 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00035.json.gz | 1131063 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00036.json.gz | 1130563 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00037.json.gz | 1132191 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00038.json.gz | 1129525 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00039.json.gz | 1132928 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00040.json.gz | 1129294 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00041.json.gz | 1132113 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00042.json.gz | 1130148 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00043.json.gz | 1131876 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00044.json.gz | 1130532 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00045.json.gz | 1131416 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00046.json.gz | 1129895 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00047.json.gz | 1131783 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00048.json.gz | 1130096 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00049.json.gz | 1029292 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00050.json.gz | 1130561 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00051.json.gz | 1131530 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00052.json.gz | 1130756 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00053.json.gz | 1131863 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00054.json.gz | 1131682 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00055.json.gz | 1131434 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00056.json.gz | 1131718 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00057.json.gz | 1130867 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00058.json.gz | 1132236 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00059.json.gz | 1129570 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00060.json.gz | 1132199 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00061.json.gz | 1129919 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00062.json.gz | 1132153 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00063.json.gz | 1129342 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00064.json.gz | 1130756 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00065.json.gz | 1128749 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00066.json.gz | 1130909 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00067.json.gz | 1129313 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00068.json.gz | 1130737 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00069.json.gz | 1129859 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00070.json.gz | 1129227 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00071.json.gz | 1130914 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00072.json.gz | 1128763 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00073.json.gz | 1131974 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00074.json.gz | 1129253 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00075.json.gz | 1131504 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00076.json.gz | 1127804 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00077.json.gz | 1124935 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00078.json.gz | 1125788 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00079.json.gz | 1124234 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00080.json.gz | 1127425 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00081.json.gz | 1125287 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00082.json.gz | 1125638 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00083.json.gz | 1126641 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00084.json.gz | 1125088 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00085.json.gz | 1127482 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00086.json.gz | 1125056 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00087.json.gz | 1126176 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00088.json.gz | 1127239 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00089.json.gz | 1125374 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00090.json.gz | 1128338 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00091.json.gz | 1126333 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00092.json.gz | 1126551 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00093.json.gz | 1127110 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00094.json.gz | 1125820 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00095.json.gz | 1127235 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00096.json.gz | 1125988 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00097.json.gz | 1125057 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00098.json.gz | 1126922 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00099.json.gz | 1124737 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00100.json.gz | 1124765 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00101.json.gz | 1125357 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00102.json.gz | 1123446 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00103.json.gz | 1126631 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00104.json.gz | 1124622 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00105.json.gz | 1125377 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00106.json.gz | 1126544 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00107.json.gz | 1124555 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00108.json.gz | 1125102 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00109.json.gz | 1126114 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00110.json.gz | 1124916 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00111.json.gz | 1125456 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00112.json.gz | 1126473 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00113.json.gz | 1125107 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00114.json.gz | 1127139 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00115.json.gz | 1127749 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00116.json.gz | 1125771 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00117.json.gz | 1127414 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00118.json.gz | 1127670 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00119.json.gz | 1125984 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00120.json.gz | 1127789 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00121.json.gz | 1128054 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00122.json.gz | 1126581 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00123.json.gz | 1127988 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00124.json.gz | 1128518 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00125.json.gz | 1126691 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00126.json.gz | 1127473 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00127.json.gz | 1128124 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00128.json.gz | 1126546 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00129.json.gz | 1127055 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00130.json.gz | 1128293 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00131.json.gz | 1126491 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00132.json.gz | 1126728 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00133.json.gz | 1128375 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00134.json.gz | 1127279 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00135.json.gz | 917528 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00136.json.gz | 1128747 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00137.json.gz | 1128167 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00138.json.gz | 1127252 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00139.json.gz | 1128617 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00140.json.gz | 1130983 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00141.json.gz | 1129937 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00142.json.gz | 1129840 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00143.json.gz | 1131496 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00144.json.gz | 1131720 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00145.json.gz | 1129675 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00146.json.gz | 1129786 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00147.json.gz | 1129341 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00148.json.gz | 1130611 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00149.json.gz | 1131622 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00150.json.gz | 1130200 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00151.json.gz | 1130307 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00152.json.gz | 1129426 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00153.json.gz | 1131421 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00154.json.gz | 1131662 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00155.json.gz | 1130426 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00156.json.gz | 1130523 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00157.json.gz | 1130015 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00158.json.gz | 1131517 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00159.json.gz | 1131307 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00160.json.gz | 1131564 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00161.json.gz | 1130967 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00162.json.gz | 1130684 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00163.json.gz | 1131285 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00164.json.gz | 1132065 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00165.json.gz | 1132913 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00166.json.gz | 1131959 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00167.json.gz | 1132020 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00168.json.gz | 1131736 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00169.json.gz | 1131976 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00170.json.gz | 1132787 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00171.json.gz | 1133333 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00172.json.gz | 1132464 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00173.json.gz | 1132633 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00174.json.gz | 1132109 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00175.json.gz | 1132311 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00176.json.gz | 1134081 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00177.json.gz | 1135041 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00178.json.gz | 1134317 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00179.json.gz | 1134083 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00180.json.gz | 1134131 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00181.json.gz | 1027237 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00182.json.gz | 1135165 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00183.json.gz | 1134983 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00184.json.gz | 1135987 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00185.json.gz | 1134594 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00186.json.gz | 1134142 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00187.json.gz | 1133954 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00188.json.gz | 1134019 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00189.json.gz | 1133308 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00190.json.gz | 1134725 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00191.json.gz | 1133942 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00192.json.gz | 1134780 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00193.json.gz | 1134519 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00194.json.gz | 1133476 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00195.json.gz | 1133602 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00196.json.gz | 1133735 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00197.json.gz | 1133410 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00198.json.gz | 1133854 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00199.json.gz | 1027955 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00200.json.gz | 1133841 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00201.json.gz | 1135019 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00202.json.gz | 1133875 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00203.json.gz | 1133522 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00204.json.gz | 1133916 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00205.json.gz | 1133769 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00206.json.gz | 1133140 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00207.json.gz | 1134445 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00208.json.gz | 1134589 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00209.json.gz | 1134815 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00210.json.gz | 1135204 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00211.json.gz | 1134643 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00212.json.gz | 1134886 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00213.json.gz | 1134989 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00214.json.gz | 1134490 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00215.json.gz | 1134277 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00216.json.gz | 1136769 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00217.json.gz | 1135918 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00218.json.gz | 1136991 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00219.json.gz | 1136646 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00220.json.gz | 1135943 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00221.json.gz | 1136228 |
| financial_company_basic_info | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl | financial_company_basic_info/api_GetFnCoBasiInfoService_getFnCoOutl/page_00222.json.gz | 1077579 |
| financial_company_basic_info | financial_company_basic_info | financial_company_basic_info/data_go_kr_catalog_15043232_openapi.json | 2165 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/anyang_medical_institutions_3079492.csv | 90378 |
| hira_hospital_info | hira_hospital_info/api_hospInfoServicev2_getHospBasisList | hira_hospital_info/api_hospInfoServicev2_getHospBasisList/page_00001.json.gz | 883266 |
| hira_hospital_info | hira_hospital_info/api_hospInfoServicev2_getHospBasisList | hira_hospital_info/api_hospInfoServicev2_getHospBasisList/page_00002.json.gz | 869654 |
| hira_hospital_info | hira_hospital_info/api_hospInfoServicev2_getHospBasisList | hira_hospital_info/api_hospInfoServicev2_getHospBasisList/page_00003.json.gz | 863802 |
| hira_hospital_info | hira_hospital_info/api_hospInfoServicev2_getHospBasisList | hira_hospital_info/api_hospInfoServicev2_getHospBasisList/page_00004.json.gz | 867463 |
| hira_hospital_info | hira_hospital_info/api_hospInfoServicev2_getHospBasisList | hira_hospital_info/api_hospInfoServicev2_getHospBasisList/page_00005.json.gz | 856869 |
| hira_hospital_info | hira_hospital_info/api_hospInfoServicev2_getHospBasisList | hira_hospital_info/api_hospInfoServicev2_getHospBasisList/page_00006.json.gz | 853960 |
| hira_hospital_info | hira_hospital_info/api_hospInfoServicev2_getHospBasisList | hira_hospital_info/api_hospInfoServicev2_getHospBasisList/page_00007.json.gz | 818786 |
| hira_hospital_info | hira_hospital_info/api_hospInfoServicev2_getHospBasisList | hira_hospital_info/api_hospInfoServicev2_getHospBasisList/page_00008.json.gz | 825851 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/daejeon_donggu_medical_institutions_3081086.csv | 27560 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/data_go_kr_catalog_15000890_fileData.json | 1450 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/data_go_kr_catalog_15001698_openapi.json | 1462 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/data_go_kr_catalog_15036627_fileData.json | 1448 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/data_go_kr_catalog_15045024_fileData.json | 1555 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/data_go_kr_catalog_15156506_fileData.json | 1752 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/data_go_kr_catalog_3072692_fileData.json | 1540 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/data_go_kr_catalog_3079492_fileData.json | 1691 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/data_go_kr_catalog_3081086_fileData.json | 1591 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/gimpo_medical_institutions_15036627.csv | 60740 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/mohw_national_public_health_medical_institutions_3072692.csv | 530716 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/nhis_health_screening_institutions_15156506.csv | 1685089 |
| hira_hospital_info | hira_hospital_info | hira_hospital_info/seongnam_medical_institutions_15000890.csv | 295354 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000001.json.gz | 910 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000002.json.gz | 1252 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000003.json.gz | 1357 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000004.json.gz | 1319 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000005.json.gz | 1227 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000006.json.gz | 1252 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000007.json.gz | 1219 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000008.json.gz | 1210 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000009.json.gz | 1309 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000010.json.gz | 1284 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000011.json.gz | 1297 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000012.json.gz | 1263 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000013.json.gz | 1265 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000014.json.gz | 1301 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000015.json.gz | 1279 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000016.json.gz | 1210 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000017.json.gz | 1252 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000018.json.gz | 1238 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000019.json.gz | 1163 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000020.json.gz | 1171 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000021.json.gz | 1335 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000022.json.gz | 1194 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000023.json.gz | 1210 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000024.json.gz | 1307 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000025.json.gz | 1385 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000026.json.gz | 1291 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000027.json.gz | 1300 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000028.json.gz | 1359 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000029.json.gz | 1244 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000030.json.gz | 1212 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000031.json.gz | 1333 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000032.json.gz | 1259 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000033.json.gz | 1277 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000034.json.gz | 1234 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000035.json.gz | 1316 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000036.json.gz | 1304 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000037.json.gz | 1214 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000038.json.gz | 1350 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000039.json.gz | 1323 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000040.json.gz | 1301 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000041.json.gz | 1229 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000042.json.gz | 1230 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000043.json.gz | 1127 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000044.json.gz | 1236 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000045.json.gz | 1207 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000046.json.gz | 1229 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000047.json.gz | 1151 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000048.json.gz | 1234 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000049.json.gz | 1257 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000050.json.gz | 1183 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000051.json.gz | 1166 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000052.json.gz | 1189 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000053.json.gz | 1188 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000054.json.gz | 1209 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000055.json.gz | 1217 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000056.json.gz | 1191 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000057.json.gz | 1305 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000058.json.gz | 1173 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000059.json.gz | 1331 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000060.json.gz | 1188 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000061.json.gz | 1247 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000062.json.gz | 1267 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000063.json.gz | 1234 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000064.json.gz | 1232 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000065.json.gz | 1308 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000066.json.gz | 1323 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000067.json.gz | 1299 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000068.json.gz | 1206 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000069.json.gz | 1260 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000070.json.gz | 1192 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000071.json.gz | 1227 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000072.json.gz | 1308 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000073.json.gz | 1246 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000074.json.gz | 1236 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000075.json.gz | 1241 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000076.json.gz | 1255 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000077.json.gz | 1220 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000078.json.gz | 1267 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000079.json.gz | 1199 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000080.json.gz | 1226 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000081.json.gz | 1221 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000082.json.gz | 1164 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000083.json.gz | 1186 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000084.json.gz | 1148 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000085.json.gz | 1190 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000086.json.gz | 1286 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000087.json.gz | 1265 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000088.json.gz | 1254 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000089.json.gz | 1254 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000090.json.gz | 1270 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000091.json.gz | 1261 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000092.json.gz | 1199 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000093.json.gz | 1236 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000094.json.gz | 1260 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000095.json.gz | 1137 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000096.json.gz | 987 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000097.json.gz | 900 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000098.json.gz | 886 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000099.json.gz | 950 |
| nts_business_status | nts_business_status/api_nts_businessman_status | nts_business_status/api_nts_businessman_status/batch_000100.json.gz | 1039 |
| pps_nara_marketplace | pps_nara_marketplace | pps_nara_marketplace/data_go_kr_catalog_15129466_openapi.json | 1442 |
| road_name_address | road_name_address | road_name_address/data_go_kr_catalog_15096712_openapi.json | 1534 |

## Stop Conditions Still Active

- No M4 score tuning is allowed from these downloads alone.
- Downloaded rows are detector candidates only, not gold labels.
- Public-record personal data remains PII; context changes action/risk/context labels, not detection existence.
- Reviewer-approved labels are still required before probability/logLR and score changes.
