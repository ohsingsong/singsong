# 🛒 쇼핑 리스트

Streamlit으로 만든 가벼운 쇼핑 리스트 앱입니다.

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 http://localhost:8501 이 열립니다.

데이터는 `data/shopping_list.json`에 저장됩니다. 앱이 처음 저장할 때 자동으로 생성됩니다.

## 테스트

```bash
pip install pytest playwright pytest-playwright
playwright install chromium
pytest tests/test_app.py
```

테스트는 별도 포트에 Streamlit 서버를 직접 띄우고 임시 데이터 파일을 사용하므로, 실제 `data/shopping_list.json`은 건드리지 않습니다.
