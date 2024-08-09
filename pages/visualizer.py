from st_link_analysis import NodeStyle, EdgeStyle, st_link_analysis, Event
import streamlit as st
from db import get_notes_with_tags, get_all_tags, get_tag_name_by_id, get_links_for_notes, get_readable_note_details




def prepare_rendering_data(user_id, selected_tags):
    # Получаем все тэги для фильтрации
    tags = get_all_tags(user_id)
    tags_titles = list(tags.keys())
    # Преобразуем выбранные тэги в их ObjectId
    tag_ids = [tags[tag] for tag in selected_tags if tag in tags]
    
    # Получаем заметки, соответствующие выбранным тэгам
    notes = get_notes_with_tags(user_id, tag_ids)

    # Создаем узлы и связи для графа
    nodes = []
    edges = []
    note_ids = []
    for note in notes:
        # Получаем имена тегов
        node_tags = [get_tag_name_by_id(tag) for tag in note["tags"]]
        
        # Добавляем узлы
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

    # Получаем связи между заметками
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

@st.dialog("Заметка", width='large')
def print_note_dialog(note_id):
    note_info = get_readable_note_details(note_id)
    st.title(note_info['title'])
    st.write(f"Тэги🏷️: {', '.join(note_info['tags']) if note_info['tags'] else 'Отсутствуют🤷‍♂️'}")
    st.write(f"Связанные заметки(линки🔗): {'<->'.join(note_info['links']) if note_info['links'] else 'Не указано'}")
    with st.expander('Содержание', expanded=True):
        st.write(note_info['content'], unsafe_allow_html=True)

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
    node_styles = [
        NodeStyle(label='NOTE', color=settings['node_color'], caption='title', icon='description')
    ]
    edge_styles = [
        EdgeStyle(label='EDGE', color=settings['edge_color'], labeled=False, directed=settings['directed'], curve_style=settings['edge_curve']),
    ]
    layout = {'name': settings['layout'], 'animate': 'end', 'componentSpacing': 80}



    # убрать кнопку удаления заметки
    def onchange_callback():
        val = st.session_state["xyz"]
        if val["action"] == "expand":
            node_id = val["data"]["node_ids"][0]  # Получаем ID узла
            print_note_dialog(node_id)
        elif val["action"] == "remove":
            pass

    st_link_analysis(elements=elements, node_styles=node_styles, edge_styles=edge_styles, layout=layout, enable_node_actions=True, on_change=onchange_callback, height=500, key='xyz')

if __name__ == "__main__":
    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        show_visualizer()
