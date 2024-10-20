import streamlit as st
import streamlit_antd_components as sac
from streamlit_navigation_bar import st_navbar
from werkzeug.security import generate_password_hash
from validators import is_password_strong, is_login_valid
from time import sleep
st.set_page_config(
    page_title='BrainGrokker',
    page_icon='🧠',
    layout='wide',
    initial_sidebar_state='collapsed'
)
from sidebar import sidebar
from db import authenticate_user, register_user, load_user_settings, get_user_by_login
import pages as pg

_INFO = """# Добро пожаловать в BrainGrokker!🧠

**BrainGrokker** — это революционная платформа для управления знаниями, которая позволяет пользователям не только сохранять заметки, но и визуализировать их взаимосвязи. Мы стремимся превратить обычный процесс ведения заметок в динамичное и взаимодействующее приключение, которая позволит вам начать не просто ‘бездумно зубрить’, а действительно понимать.

**Наша миссия** — облегчить процесс усвоения информации и повысить продуктивность за счет интуитивно понятных инструментов визуализации и управления знаниями. BrainGrokker делает обучение и организацию знаний более эффективными и менее утомительными. 

**Ключевые возможности:**
- **Визуализация связей:** BrainGrokker использует современные технологии для отображения и управления связями между заметками, что позволяет пользователям видеть большую картину их знаний.
- **Удобный интерфейс:** Простой и понятный интерфейс делает процесс работы с заметками лёгким и приятным.

**Для кого это приложение?**
BrainGrokker идеально подходит для студентов, исследователей, писателей и всех, кто регулярно работает с большим объемом информации. Если вы ищете способ улучшить свою учебу или работу, наша платформа станет вашим незаменимым помощником.

**Присоединяйтесь к нам в путешествии по миру знаний!**
"""
PAGES = ['Главная', 'Заметки', 'Визуализатор', 'О проекте']
STYLES = {
    "nav": {
        "background-color": "#1c1c1c",  # Темный фон для навигации
        "font-size"
        "font-family": "monospace"
    },
    "div": {
        "max-width": "32rem",  # Ограничение ширины
    },
    "span": {
        "border-radius": "0.5rem",
        "color": "#d3d3d3",  # Светло-серый цвет текста
        "margin": "0 0.125rem",
        "padding": "0.4375rem 0.625rem",
        "font-size": "1.125rem"
    },
    "active": {
        "background-color": "rgba(40, 195, 160, 1)",  # Основной зеленый цвет для активного элемента
        "color": "#1c1c1c",  # Темный текст для контраста
        "font-family": "monospace",
        "font-weight": "bold",  # Жирный текст для выделения
    },
    "hover": {
        "background-color": "rgba(40, 195, 160, 0.7)",  # Полупрозрачный зеленый при наведении
        "color": "#ffffff",  # Белый текст для хорошего контраста
    },
}
OPTIONS = {
    "show_menu": True,
    "show_sidebar": True,
    "hide_nav": True,
    "use_padding": False
}



def authorisation_page():
    def login_form():
        """ Форма входа """
        with st.form("login_form"):
            st.markdown("**Войти в систему**")
            login_userid = st.text_input("Логин")
            st.write('')
            login_password = st.text_input("Пароль", type="password")
            login_button = st.form_submit_button("Войти")
            if login_button:
                user_id = authenticate_user(login_userid, login_password)
                if user_id:
                    st.session_state['user_login'] = login_userid
                    st.session_state['user_id'] = user_id
                    st.session_state['authenticated'] = True
                    st.session_state['settings'] = load_user_settings(user_id)
                    st.rerun()
                else:
                    st.error("Ошибка")
    def register_form():
        """ Форма регистрации """
        with st.form("register_form"):
            st.markdown("**Регистрация**")
            user_login = st.text_input("Логин", help="**Должен быть длиной от 5 до 20 символов**")
            st.write('')
            st.write('')

            user_password = st.text_input("Пароль", type="password", help="**Цифра, заглавная и строчная буква, 8 <  < 20 символов**")
            submit_button = st.form_submit_button("Зарегистрировать")

            if submit_button:
                if not is_login_valid(user_login):
                    st.error("Логин должен быть длиной от 5 до 20 символов.")
                elif get_user_by_login(user_login) is not None:
                    st.error("Этот логин уже используется.")
                elif not is_password_strong(user_password):
                    st.error("Пароль не соответствует требованиям безопасности.")
                else:
                    registration_result = register_user(login=user_login, password_hash=generate_password_hash(user_password))
                    st.session_state['user_login'] = user_login
                    st.session_state['user_id'] = registration_result
                    st.session_state['authenticated'] = True
                    st.session_state['settings'] = load_user_settings(registration_result)
                    st.rerun()
    def info():
        def stream_data():
            for word in _INFO.split(" "):
                yield word + " "
                sleep(0.05)
        st.write_stream(stream_data())


    sac.tabs([
        sac.TabsItem(label='О нас', icon='bi bi-info-circle'),
        sac.TabsItem(label='Войти', icon='bi bi-box-arrow-in-right'),
        sac.TabsItem(label='Зарегистрироваться', icon='plus-square')
    ], height=150, size='xl', format_func='title', align='center', variant='outline', index = 0, use_container_width=True, key='tab')
    TABS = {
            'Войти': login_form,
            'Зарегистрироваться': register_form,
            'О нас': info
        }
    def navigate():
        tab_name = st.session_state.tab  
        if tab_name in TABS:
            tab_func = TABS[tab_name]
            tab_func()  
    navigate()

functions = {
    "Главная": pg.display_activity_metrics,
    "Заметки": pg.create_note_component,
    "Визуализатор": pg.show_visualizer,
    "О проекте": pg.show_about
}

if 'authenticated' in st.session_state and st.session_state.authenticated:
    sidebar()
    page = st_navbar(
    PAGES,
    styles=STYLES,
    options=OPTIONS,
    )
    go_to = functions.get(page)
    if go_to:
        go_to()
        
    
else:
    authorisation_page()


