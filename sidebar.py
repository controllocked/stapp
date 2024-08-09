import streamlit as st
import streamlit_antd_components as sac
from db import save_user_settings
from st_link_analysis.component.layouts import LAYOUTS

THEMES = [
    "chaos", "cobalt", "dracula", "gruvbox", "idle_fingers", 
    "kr_theme", "merbivore", "merbivore_soft", "mono_industrial", "monokai",
    "nord_dark", "pastel_on_dark", "solarized_dark", "terminal",
    "tomorrow_night", "tomorrow_night_blue", "tomorrow_night_bright",
    "tomorrow_night_eighties", "twilight", "vibrant_ink"
]
CURVE_STYLES = [
    "bezier",
    "haystack",
    "straight",
    "unbundled-bezier",
    "round-segments",
    "segments",
    "round-taxi",
    "taxi",
]
LAYOUT_NAMES = list(LAYOUTS.keys())

def sidebar():
    if 'settings_temp' in st.session_state:
        st.session_state['settings'].update(st.session_state['settings_temp'])
    else:
        st.session_state['settings_temp'] = st.session_state['settings'].copy()

    with st.sidebar:
        if st.button("Выйти из аккаунта"):
            st.session_state.clear()
            st.rerun()
        st.divider()
        st.subheader("Настройки приложения")
    
        with st.expander("Настройки редактора текста"):
            with st.form('ace', border=False):
                ace_theme = st.selectbox("Тема редактора", options=THEMES, index=THEMES.index(st.session_state['settings_temp']['ace_theme']))
                ace_font_size = st.slider("Размер шрифта ACE", min_value=5, max_value=24, value=st.session_state['settings_temp']['ace_font_size'])
                language = st.radio('Форматирование текста', 
                                    options=['plain_text', 'markdown'],
                                    captions=['Обычный сплошной текст для самых маленьких🐤', 
                                            'Мощный инструмент для продвинутых юзеров😎, подробнее [на википедии](https://ru.wikipedia.org/wiki/Markdown)'],
                                    help='Выберите как будет отображаться содержание заметок'
                )
                show_gutter = st.toggle("Показывать gutter", value=st.session_state['settings_temp']['show_gutter'], help='Отображает номера линий + дает возможность скрывать блоки')
                
                if st.form_submit_button('Применить (2 клика)'):
                    st.session_state['settings_temp'].update({
                        'ace_theme': ace_theme,
                        'ace_font_size': ace_font_size,
                        'language': language,
                        'show_gutter': show_gutter
                    })

        with st.expander("Настройки графов"):
            with st.form('graph', border=False):
                node_color = st.color_picker("Цвет узлов", value=st.session_state['settings_temp']['node_color'])
                edge_color = st.color_picker("Цвет связей", value=st.session_state['settings_temp']['edge_color'])
                directed = st.checkbox("Направленные связи", value=st.session_state['settings_temp']['directed'])
                edge_curve = st.selectbox("Конфигурация видов связей", CURVE_STYLES, index=CURVE_STYLES.index(st.session_state['settings_temp']['edge_curve']))
                layout = st.selectbox("Конфигурация расположения узлов", LAYOUT_NAMES, index=LAYOUT_NAMES.index(st.session_state['settings_temp']['layout']))

                if st.form_submit_button('Применить (2 клика)'):
                    st.session_state['settings_temp'].update({
                        'node_color': node_color,
                        'edge_color': edge_color,
                        'directed': directed,
                        'edge_curve': edge_curve,
                        'layout': layout
                    })

        if st.button("Сохранить настройки"):
            save_user_settings(st.session_state['user_id'], st.session_state['settings'])
            st.success("Настройки сохранены", icon="✅")

        # Здесь может быть функционал для отображения списка заметок и их навигации


if __name__ == '__main__':
    sidebar()
