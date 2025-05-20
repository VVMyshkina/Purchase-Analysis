import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from datetime import datetime, timedelta

# Настройка стиля графиков
sns.set_style("whitegrid")

# Кеширование данных для ускорения
@st.cache_data(ttl=300)
def get_products():
    url = "http://localhost:5000/get_products"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при загрузке продуктов: {str(e)}")
        return []

@st.cache_data(ttl=300)
def get_categories():
    url = "http://localhost:5000/get_categories"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при загрузке категорий: {str(e)}")
        return []

@st.cache_data(ttl=300)
def get_date_range():
    url = "http://localhost:5000/get_date_range"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if 'error' in data:
            st.error(f"Ошибка при загрузке диапазона дат: {data['error']}")
            return datetime.now().date(), datetime.now().date()
        min_date = pd.to_datetime(data['min_date']).date()
        max_date = pd.to_datetime(data['max_date']).date()
        return min_date, max_date
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при загрузке диапазона дат: {str(e)}")
        return datetime.now().date(), datetime.now().date()

def get_aggregate_data(product_id, start_date, end_date, aggregate_type, group_by):
    url = "http://localhost:5000/get_aggregate"
    params = {
        'product_id': str(product_id),
        'start_date': start_date,
        'end_date': end_date,
        'aggregate_type': aggregate_type,
        'group_by': group_by
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and 'error' in data:
            st.error(f"Ошибка API: {data['error']}")
            return pd.DataFrame()
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при загрузке данных: {str(e)}")
        return pd.DataFrame()

# UI в Streamlit
st.title("Анализ и визуализация")
st.write("Настройте параметры для анализа данных")

# Выбор категории (опционально)
categories = get_categories()
selected_category = st.selectbox("Выберите категорию (опционально)", ["Все"] + categories)

# Выбор продукта
products = get_products()
if selected_category != "Все":
    # TODO: Реализовать фильтрацию по категории через API, если нужно
    products = [p for p in products]
if products:
    selected_product = st.selectbox("Выберите продукт", products)
else:
    st.warning("Нет доступных продуктов для выбранной категории")
    selected_product = None

# Выбор временного интервала
min_date, max_date = get_date_range()
date_range = st.date_input("Выберите диапазон дат", [min_date, max_date], min_value=min_date, max_value=max_date)

# Выбор типа агрегата
aggregate_type_display = st.selectbox("Выберите тип агрегата", ["Количество покупок", "Сумма продаж"])
aggregate_type = 'count' if aggregate_type_display == "Количество покупок" else 'sum'

# Выбор интервала группировки
group_by_display = st.selectbox("Группировать по", ["День", "Неделя", "Месяц"])
group_by_map = {
    "День": "day",
    "Неделя": "week",
    "Месяц": "month"
}
group_by = group_by_map[group_by_display]

# Получение и обработка данных
if selected_product:
    start_date_str = date_range[0].strftime('%Y-%m-%d')
    end_date_str = date_range[1].strftime('%Y-%m-%d')
    agg_df = get_aggregate_data(
        product_id=selected_product,
        start_date=start_date_str,
        end_date=end_date_str,
        aggregate_type=aggregate_type,
        group_by=group_by
    )

    # Визуализация
    if not agg_df.empty:
        agg_df['time'] = pd.to_datetime(agg_df['time'])
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=agg_df, x='time', y='value', marker='o')
        plt.title(f"{aggregate_type_display} для {selected_product} по {group_by_display.lower()}ам")
        plt.xlabel("Время")
        plt.ylabel(aggregate_type_display)
        plt.xticks(rotation=45)
        st.pyplot(plt)
    else:
        st.warning("Нет данных для выбранных параметров. Проверьте диапазон дат или продукт.")

    # Показать таблицу с данными
    st.subheader("Таблица с данными")
    st.dataframe(agg_df)
else:
    st.info("Выберите продукт для отображения данных")