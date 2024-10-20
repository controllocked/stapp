import re
import streamlit as st
from streamlit_ace import st_ace
from streamlit_tags import st_tags
from bson.objectid import ObjectId
from db import get_notes_by_user_id, get_all_tags, create_note, add_tag

THEMES = [
    "chaos", "cobalt", "dracula", "gruvbox", "idle_fingers", 
    "kr_theme", "merbivore", "merbivore_soft", "mono_industrial", "monokai",
    "nord_dark", "pastel_on_dark", "solarized_dark", "terminal",
    "tomorrow_night", "tomorrow_night_blue", "tomorrow_night_bright",
    "tomorrow_night_eighties", "twilight", "vibrant_ink"
]

def parse_note_content(content):
    # Извлечение заголовка
    title = re.search(r'^#\s*(.+)', content, re.MULTILINE)
    title = title.group(1) if title else "Без названия"

    # Извлечение краткого содержания
    summary = re.search(r'@sum\((.*?)\)', content)
    summary = summary.group(1) if summary else "Без краткого содержания"

    return title, summary

def highlight_content(content):
    """Подсвечивает тэги и линки в содержимом мягкими цветами"""
    content = re.sub(r'^#\s*(.+)', r'<h1 style="color:lightgreen;">\1</h1>', content)  # Тэги зелёным цветом
    content = re.sub(r'@sum\((.*?)\)', r'<strong>Краткое содержание:</strong> \1', content)  # Краткое содержание жирным
    return content

def create_note_component():
    st.title('Создание/Редактирование заметки')
    left, right = st.columns(2)
    with left:
        settings = st.session_state['settings']
        st.write('Содержание заметки')
        with st.container(height=600):
            content = st_ace(
                placeholder='Начинайте творить',
                value=st.session_state.get('content', ''),
                language=settings['language'],
                theme=settings['ace_theme'],
                keybinding='vscode',
                font_size=settings['ace_font_size'],
                tab_size=4,
                show_gutter=settings['show_gutter'],
                wrap=True,   
                height=500,
                key='editor_content'
            )
            st.session_state['content'] = content

    with right:
        st.write('Предварительный просмотр')
        
        # Отображение заголовка, краткого содержания
        title, summary = parse_note_content(content)
        
        with st.container(border=True, height=470):
            highlighted_content = highlight_content(content)
            st.markdown(highlighted_content, unsafe_allow_html=True)
        notes = get_notes_by_user_id(st.session_state['user_id'])
        with st.container(height=122, border=True):
            l, r = st.columns(2, gap='large')
            with l:
                links = st.multiselect("###### Относящиеся заметки-линки (Рекомендуется)",
                                        options=list(notes.keys()),
                                        placeholder='Названия заметок',
                                        default=st.session_state['addition'][0].keys() if 'addition' in st.session_state else [])
            # Подсветка содержимого
            with r:
                existing_tags = get_all_tags(st.session_state['user_id'])
                tags_titles = list(existing_tags.keys())
                tags = st_tags(
                    label='Тэги, связанные с заметкой (Рекомендуется)',
                    text='',
                    suggestions=tags_titles,
                    maxtags=20,
                    value=st.session_state['secinfo']['existing_tags']+st.session_state['secinfo']['new_tags'] if 'secinfo' in st.session_state else ''
                )
                new_tags = []
                for tag in tags:
                    if tag not in tags_titles:
                        new_tags.append(tag)

    # Сохранение заметки и очистка session_state
    if st.button('Сохранить'):
        notes_by_user = get_notes_by_user_id(st.session_state['user_id'])
        
        # Проверяем, что заголовок уникален
        if title and title not in notes_by_user:
            # Генерация объектов ObjectId для тэгов
            tag_objects = [ObjectId(add_tag(tag, st.session_state['user_id'])) for tag in tags]
            
            # Генерация ObjectId для связанных заметок по названию заметки
            linked_notes = []
            for note_title in links:
                note_id = notes_by_user.get(note_title)  # Получаем ObjectId по названию заметки
                if note_id:  # Проверяем, что заметка существует
                    linked_notes.append(ObjectId(note_id))
                else:
                    st.warning(f'Заметка "{note_title}" не найдена и не будет добавлена в связи.')

            # Сохранение новой заметки
            create_note(
                user_id=st.session_state['user_id'],
                content=content,
                title=title,
                summary=summary,
                tags=tag_objects,
                links=linked_notes
            )
            st.success(f'Заметка "{title}" успешно сохранена!')

            # Очистка session_state для новой заметки
            st.session_state.pop('content', None)
            st.session_state.pop('secinfo', None)
            st.session_state.pop('addition', None)
        else:
            st.warning("Заметка с таким заголовком уже существует или его нет")

if __name__ == "__main__":
    st.session_state
    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        create_note_component()