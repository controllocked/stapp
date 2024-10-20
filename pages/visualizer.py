import re
import streamlit as st
from streamlit_ace import st_ace
from streamlit_tags import st_tags
from bson.objectid import ObjectId
from st_link_analysis import NodeStyle, EdgeStyle, st_link_analysis
from db import get_notes_with_tags, get_notes_by_user_id, get_all_tags, get_tag_name_by_id, get_links_for_notes, get_readable_note_details, create_note, add_tag, update_note, delete_note

def parse_note_content(content):
    title = re.search(r'^#\s*(.+)', content, re.MULTILINE)
    title = title.group(1) if title else "Без названия"
    summary = re.search(r'@sum\((.*?)\)', content)
    summary = summary.group(1) if summary else "Без краткого содержания"
    return title, summary

def highlight_content(content):
    content = re.sub(r'^#\s*(.+)', r'<h1 style="color:lightgreen;">\1</h1>', content)
    content = re.sub(r'@sum\((.*?)\)', r'<strong>Краткое содержание:</strong> \1', content)
    return content

@st.dialog("Заметка", width='large')
def create_edit_note_dialog(note_id=None):
    # Инициализация ключей в session_state, если они отсутствуют
    if 'original_content' not in st.session_state:
        st.session_state['original_content'] = ''
    if 'original_tags' not in st.session_state:
        st.session_state['original_tags'] = []
    if 'original_links' not in st.session_state:
        st.session_state['original_links'] = []

    # Используем фиксированный ключ для текущей заметки
    if note_id != st.session_state.get('current_note_id'):
        st.session_state['current_note_id'] = note_id
        if note_id:
            note_info = get_readable_note_details(note_id)
            st.session_state['original_content'] = note_info['content']  # Оригинальный контент для сравнения
            st.session_state['original_tags'] = note_info['tags']  # Оригинальные тэги для сравнения
            st.session_state['original_links'] = note_info['links']  # Оригинальные линки для сравнения
            st.session_state['content'] = note_info['content']
            st.session_state['existing_tags'] = note_info['tags']
            st.session_state['links'] = note_info['links']
        else:
            st.session_state['content'] = ''
            st.session_state['original_content'] = ''
            st.session_state['original_tags'] = []
            st.session_state['original_links'] = []
            st.session_state['existing_tags'] = []
            st.session_state['links'] = []

    left, right = st.columns(2)
    with left:
        settings = st.session_state['settings']
        st.write('Содержание заметки')
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
            key=f'editor_content'
        )
        st.session_state['content'] = content  # Обновляем состояние

    with right:
        st.write('Предварительный просмотр')
        title, summary = parse_note_content(content)
        
        with st.container(border=True, height=470):
            highlighted_content = highlight_content(content)
            st.markdown(highlighted_content, unsafe_allow_html=True)

        notes = get_notes_by_user_id(st.session_state['user_id'])
        links = st.multiselect("###### Относящиеся заметки-линки",
                                options=list(notes.keys()),
                                placeholder='Названия заметок',
                                default=st.session_state['links'])
        st.session_state['links'] = links

        existing_tags = get_all_tags(st.session_state['user_id'])
        tags_titles = list(existing_tags.keys())
        tags = st_tags(
            label='Тэги, связанные с заметкой',
            text='',
            suggestions=tags_titles,
            maxtags=20,
            value=st.session_state['existing_tags'],
            key='tags'
        )
        st.session_state['existing_tags'] = tags

    if st.button('Закрыть'):
        title, summary = parse_note_content(st.session_state['content'])
        
        tag_objects = [ObjectId(add_tag(tag, st.session_state['user_id'])) for tag in tags]
        linked_notes = [ObjectId(get_notes_by_user_id(st.session_state['user_id'])[note]) for note in links if note in get_notes_by_user_id(st.session_state['user_id'])]

        # Проверка: если контент, теги или ссылки изменились, то обновляем заметку
        if note_id and (
            st.session_state['content'] != st.session_state['original_content'] or
            st.session_state['existing_tags'] != st.session_state['original_tags'] or
            st.session_state['links'] != st.session_state['original_links']
        ):
            update_note(note_id, content=content, tags=tag_objects, links=linked_notes)
        elif note_id is None:  # Создание новой заметки
            create_note(
                user_id=st.session_state['user_id'],
                content=content,
                title=title,
                summary=summary,
                tags=tag_objects,
                links=linked_notes
            )

        # Очищаем состояние и обновляем граф
        st.session_state['content'] = ''
        st.session_state['original_content'] = ''
        st.session_state['original_tags'] = []
        st.session_state['original_links'] = []
        st.session_state['existing_tags'] = []
        st.session_state['links'] = []
        st.session_state['current_note_id'] = None
        st.rerun()

def prepare_rendering_data(user_id, selected_tags):
    tags = get_all_tags(user_id)
    tag_ids = [tags[tag] for tag in selected_tags if tag in tags]
    notes = get_notes_with_tags(user_id, tag_ids)

    nodes = []
    edges = []
    note_ids = []
    for note in notes:
        node_tags = [get_tag_name_by_id(tag) for tag in note["tags"]]
        nodes.append({
            'data': {
                "id": str(note["_id"]),
                "label": "NOTE",
                "title": note["title"],
                "description": note["summary"],
                "tags": ", ".join(node_tags),
            }
        })
        note_ids.append(note["_id"])

    linked_notes = get_links_for_notes(note_ids)
    for note in linked_notes:
        for link in note["links"]:
            edges.append({
                'data': {
                    "id": f"{str(note['_id'])}_{str(link)}",
                    "label": "EDGE",
                    "source": str(note["_id"]),
                    "target": str(link),
                }
            })

    return nodes, edges

def show_visualizer():
    user_id = st.session_state['user_id']
    st.title('Графовая визуализация〇')
    with st.expander("Настройки фильтра"):
        with st.form("filter", border=False):
            select_tags = st.multiselect("Выберите тэги для фильтрации", list(get_all_tags(user_id).keys()))
            if st.form_submit_button('Отфильтровать'):
                selected_tags = select_tags
            else:
                selected_tags = []

    nodes, edges = prepare_rendering_data(user_id, selected_tags)
    elements = {"nodes": nodes, "edges": edges}
    settings = st.session_state['settings']
    
    node_styles = [NodeStyle(label='NOTE', color=settings['node_color'], caption='title', icon='description')]
    edge_styles = [EdgeStyle(label='EDGE', color=settings['edge_color'], labeled=False, directed=settings['directed'], curve_style=settings['edge_curve'])]
    layout = {'name': settings['layout'], 'animate': 'end', 'componentSpacing': 30}

    def onchange_callback():
        val = st.session_state["xyz"]
        node_id = val["data"]["node_ids"][0]
        
        if val["action"] == "expand":
            create_edit_note_dialog(note_id=node_id)  # Открываем диалог для редактирования
        elif val["action"] == "remove":
            # Проверка на наличие связей
            linked_notes = get_links_for_notes([node_id])
            if not linked_notes:  # Если связей нет, удаляем заметку
                delete_note_result = delete_note(node_id)
                if delete_note_result:
                    st.success("Заметка успешно удалена!")
                else:
                    st.error("Ошибка при удалении заметки!")
                st.rerun()  # Обновляем граф после удаления
            else:
                st.error("Невозможно удалить заметку, она связана с другими заметками!")

    st_link_analysis(elements=elements, node_styles=node_styles, edge_styles=edge_styles, layout=layout, node_actions=["expand", "remove"], on_change=onchange_callback, height=600, key='xyz')

if __name__ == "__main__":
    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        show_visualizer()
