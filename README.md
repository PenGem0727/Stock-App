# 미국 주식 리서치 대시보드

개인 투자자가 미국 상장 기업을 빠르게 살펴볼 수 있도록 만든 Streamlit 기반 리서치 웹앱입니다. 티커를 입력하면 차트, 재무제표, 기업 개요, 밸류에이션, 시가총액 순위를 한 화면에서 확인할 수 있습니다.

## 주요 기능

- 한국어 UI 기반 투자 리서치 대시보드
- Plotly 인터랙티브 주가 차트
- 기간 선택: 1개월, 3개월, 6개월, 1년, 3년, 5년, 최대
- 봉 종류 선택: 일봉, 주봉, 월봉
- 캔들차트 또는 라인차트 선택
- 거래량, 이동평균선, RSI 표시
- 현재가, 전일 대비 등락률, 52주 최고가/최저가, 거래량 요약
- 연간/분기 재무제표 조회
- 손익계산서, 재무상태표, 현금흐름표 표시
- 주요 재무 항목 한국어 변환
- 기업 개요, 주요 임원, 배당 정보 표시
- PER, PBR, PSR, ROE, ROA, 마진, FCF Yield 등 밸류에이션 지표 정리
- 주요 미국 상장 대형주 또는 Wikipedia S&P 500 구성종목 기반 시가총액 순위
- 검색, 섹터 필터, 상위 10개 기업 막대그래프
- Streamlit cache를 활용한 데이터 로딩 최적화

## 설치 방법

Python 3.10 이상 환경을 권장합니다.

```bash
pip install -r requirements.txt
```

가상환경을 사용하는 경우 예시는 다음과 같습니다.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 실행 방법

```bash
streamlit run app.py
```

실행 후 브라우저에서 표시되는 로컬 주소로 접속하면 됩니다.

## 사용 예시

1. 왼쪽 사이드바의 `티커 입력`에 `AAPL`, `MSFT`, `NVDA`, `TSLA`, `AMZN`, `GOOGL`, `META`, `TSM` 같은 티커를 입력합니다.
2. 기간, 봉 종류, 차트 종류를 선택합니다.
3. 이동평균선 기간과 표시 여부를 조정합니다.
4. RSI 기간을 설정합니다.
5. 상단 탭에서 `종목 차트`, `재무제표`, `기업 개요`, `밸류에이션`, `시가총액 순위`를 전환해 확인합니다.

## 데이터 출처

- 주가, 재무제표, 기업 정보, 밸류에이션 지표: [yfinance](https://pypi.org/project/yfinance/)
- 주가 및 시가총액 보조 데이터: Yahoo Finance 공개 JSON 엔드포인트
- 재무제표 보조 데이터: [SEC Company Facts](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- S&P 500 구성종목: [Wikipedia - List of S&P 500 companies](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies)

이 앱은 API Key가 필요 없는 공개 데이터 중심으로 구성되어 있습니다. 다만 yfinance와 공개 웹 데이터는 실시간 공식 거래소 데이터가 아니며, 데이터 지연이나 누락이 발생할 수 있습니다.

## 주의사항

- 확인되지 않은 데이터는 임의로 생성하지 않습니다.
- 데이터가 없거나 계산할 수 없는 항목은 `데이터 없음`, `확인 불가`, `계산 불가`로 표시합니다.
- 본 앱은 투자 참고용이며, 매수·매도 추천이 아닙니다.
- 실제 투자 판단에는 공식 공시, 증권사 리서치, 기업 IR 자료 등 추가 검증이 필요합니다.
- 데이터가 보이지 않는 경우 사이드바의 `데이터 새로고침` 버튼을 눌러 캐시를 초기화한 뒤 다시 조회하세요.
