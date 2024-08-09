import streamlit as st
import streamlit_antd_components as sac
from streamlit_ace import st_ace
from streamlit_tags import st_tags
from bson.objectid import ObjectId
from db import get_notes_by_user_id,  get_all_tags, create_note, add_tag


THEMES = [
    "chaos", "cobalt", "dracula", "gruvbox", "idle_fingers", 
    "kr_theme", "merbivore", "merbivore_soft", "mono_industrial", "monokai",
    "nord_dark", "pastel_on_dark", "solarized_dark", "terminal",
    "tomorrow_night", "tomorrow_night_blue", "tomorrow_night_bright",
    "tomorrow_night_eighties", "twilight", "vibrant_ink"
]


def create_note_component():
    st.title('Создание заметки📝')
    sac.steps(
        items=[
            sac.StepsItem(title='Шаг 1', 
                        subtitle='Записать основное содержание'),
            sac.StepsItem(title='Шаг 2', 
                        subtitle='Оставить информацию'),
            sac.StepsItem(title='Шаг 3',
                        subtitle='Проверить результат/опубликовать')
        ], size='sm', color="#28c3a0", key="steps", return_index=True, 
    )

    def step1():
        st.write('')


        left, right = st.columns(2)
        with left:
            settings = st.session_state['settings']
            st.write('**Содержание**')
            with st.container(height=600):
                content = st_ace(
                    placeholder = 'Начинайте писать!',
                    value = st.session_state['content'] if 'content' in st.session_state else '',
                    language = settings['language'],
                    theme = settings['ace_theme'],
                    keybinding = 'vscode',
                    font_size = settings['ace_font_size'],
                    tab_size=4,
                    show_gutter=settings['show_gutter'],
                    wrap=True,   
                    height=500,
                    key='editor_content'
                )


                # хз зачем мне editor_content, но с ним баг с дабл сохранением пропадает
                if st.session_state['editor_content']:
                    st.session_state['content'] = st.session_state['editor_content']


        with right:
            st.write('**Отражение**(Полезно для вывода markdown кода)')
            with st.container(border=True,
                              height=600):
                if settings['language'] == 'markdown':
                    st.write(content, unsafe_allow_html=True)
                else:
                    st.text(content)


           







    def step2():
        with st.form("create_note_form"):
            col1, col2 = st.columns([1, 1], gap='large')
            with col1:
                title = st.text_input('Заголовок:red[*]', 
                                    help='Заголовку следуют отражать содержание',
                                        max_chars=50,
                                        value=st.session_state['secinfo'].get('title') if 'secinfo' in st.session_state else '')
                summary = st.text_area('Краткое содержание (Рекомендуется)',
                                    help='Краткая справка про содержанрие заметки',
                                    value=st.session_state['secinfo'].get('summary') if 'secinfo' in st.session_state else '')
            with col2:
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
                
                notes = get_notes_by_user_id(st.session_state['user_id'])
                links = st.multiselect("###### Относящиеся заметки-линки (Рекомендуется)",
                                       options=list(notes.keys()),
                                       help='Выбранные заметки определяют связь в графе с другими',
                                       placeholder='Названия заметок',
                                       default=st.session_state['addition'][0].keys() if 'addition' in st.session_state else [])

            submitted = st.form_submit_button('Сохранить')
            if submitted:
                # TODO добавить проверку на уникальность названия
                if title and title not in list(notes.keys()):
                    st.toast('Информация сохранена', icon='✅')
                    st.session_state['secinfo'] = {
                        'title': title,
                        'summary': summary,
                        'existing_tags': list(filter(lambda x: x in tags_titles, tags)),
                        'new_tags': new_tags,
                        'links': [notes[title] for title in links]
                    }
                    st.session_state['addition'] = [notes, {key: value for key, value in existing_tags.items() if key in st.session_state['secinfo']['existing_tags']}]
                else:
                    st.toast('Ошибка, названия заметок не могут быть пустым/повторяться', icon='⛔️')
        
            


                
    def step3():
        def print_note():
                    info = st.session_state['secinfo']
                    st.title(info['title'])
                    st.write('Категории(тэги🏷️):')
                    st.write(
                        f"""- Новые тэги: {', '.join(st.session_state['secinfo']['new_tags']) if st.session_state['secinfo']['new_tags'] else 'Отсутствуют🤷‍♂️'}\n- Существующие тэги: {', '.join(st.session_state['secinfo']['existing_tags']) if st.session_state['secinfo']['existing_tags'] else 'Отсутствуют🤷‍♂️'}""")
                    st.write(f"Связанные заметки(линки🔗): {'<->'.join(st.session_state['addition'][0].keys()) if st.session_state['addition'][0] else 'Не указано'}")
                    with st.expander('Содержание', expanded=True):
                        st.write(st.session_state['content'], unsafe_allow_html=True)
        if 'content' in st.session_state and st.session_state['content'] and 'secinfo' in st.session_state:
            print_note()
            st.write('')
            submit = st.button('Загрузить')
            if submit:
                # Доработать здесь добавление новых тэгов в бдщ
                tag_objects_to_add = list(st.session_state['addition'][1].values())
                for new_tag in st.session_state['secinfo']['new_tags']:
                    tag_objects_to_add.append(ObjectId(add_tag(new_tag, st.session_state['user_id'])))
                essential_info = st.session_state['secinfo']
                create_note(
                    user_id=st.session_state['user_id'],
                    content=st.session_state['content'], 
                    title=essential_info['title'], 
                    summary=essential_info['summary'],
                    tags=tag_objects_to_add,
                    links=essential_info['links'])
                st.success('Заметка создана', icon='✅')
                del st.session_state['content']
                del st.session_state['secinfo']
                del st.session_state['addition']


        else:
            st.warning('Ошибка, пройдите предыдущие шаги', icon='⛔️')

        
        
            
    

    (step1, step2, step3)[st.session_state['steps']]()




if __name__ == "__main__":
    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        create_note_component()