import pandas as pd
import streamlit as st
from db import get_notes_data



def display_activity_metrics():
    st.title(f'Welcome ***{st.session_state['user_login']}***')
    user_id = st.session_state['user_id']
    data = get_notes_data(user_id)
    
    # Если нет данных, выводим сообщение
    if not data:
        st.write("Нет данных для отображения.")
        return

    # Преобразование в DataFrame и обработка дат
    df = pd.DataFrame(data)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['date'] = df['created_at'].dt.date

    # Группировка по дате
    daily_notes = df.groupby('date').size().reset_index(name='count')

    # Метрики
    max_notes = daily_notes['count'].max()
    avg_notes = daily_notes['count'].mean()
    total_notes = daily_notes['count'].sum()

    st.metric("Максимум заметок в день", max_notes)
    st.metric("Среднее количество заметок в день", f"{avg_notes:.2f}")
    st.metric("Всего заметок", total_notes)

    # График активности
    st.line_chart(daily_notes.set_index('date'))

if __name__ == "__main__":
    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        display_activity_metrics()
