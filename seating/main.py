import streamlit as st
import pandas as pd

# =============================================
# КОНФИГУРАЦИЯ ДВУХ АУДИТОРИЙ (изменяется только здесь)
# =============================================

# Первая аудитория (R503)
AUDITORIUM_101 = {
    "name": "Auditorium R503",
    "row_config": [
        # Каждый ряд задается списком парт в ряду:
        # "desk" - парта (2 места)
        # "gap" - пропуск (1 место шириной)
        # Ряд 1 (ближний)
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"],
        # Ряд 2
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"],
        # Ряд 3
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"],
        # Ряд 4
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"]
    ],
    "students": [
        "Иванов Иван Иванович", "Петров Петр Петрович", "Сидорова Анна Михайловна",
        "Кузнецов Дмитрий Сергеевич", "Смирнова Екатерина Викторовна", "Васильев Андрей Николаевич",
        "Попова Ольга Дмитриевна", "Новиков Александр Игоревич", "Федорова Мария Александровна",
        "Морозов Артем Олегович", "Волкова Юлия Сергеевна", "Алексеев Павел Денисович",
        "Лебедева Анастасия Романовна", "Козлов Игорь Вадимович", "Егорова Дарья Евгеньевна"
    ],
    "manual_assignments": {
        (1, 1): "Иванов Иван Иванович",
        (1, 2): "Петров Петр Петрович",
        (2, 1): "Сидорова Анна Михайловна"
    }
}

# Вторая аудитория (R505)
AUDITORIUM_201 = {
    "name": "Auditorium R505",
    "row_config": [
        # Ряд 1 (ближний)
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"],
        # Ряд 2
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"],
        # Ряд 3
        ["desk", "desk", "gap", "desk"],
        # Ряд 4
        ["desk", "gap", "desk", "gap", "desk"],
        # Ряд 5 (дальний)
        ["desk", "desk"]
    ],
    "students": [
        "Тарасов Никита Владимирович", "Андреева Вероника Станиславовна", "Борисов Максим Юрьевич",
        "Григорьева Елена Олеговна", "Дмитриев Константин Александрович", "Жукова Виктория Сергеевна",
        "Захаров Артемий Игоревич", "Ильина Марина Денисовна", "Крылов Станислав Валерьевич",
        "Ларина Ольга Павловна", "Миронов Денис Андреевич", "Николаева Анастасия Игоревна",
        "Осипов Владислав Артемович", "Павлова Кристина Романовна"
    ],
    "manual_assignments": {
        (1, 1): "Тарасов Никита Владимирович",
        (1, 2): "Андреева Вероника Станиславовна",
        (3, 1): "Борисов Максим Юрьевич"
    }
}

# Все доступные аудитории
AUDITORIUMS = {
    "R501": AUDITORIUM_101,
    "R505": AUDITORIUM_201
}


# =============================================
# ФУНКЦИИ (не требуют изменений)
# =============================================

def create_seating_chart(students, row_config, manual_assignments=None):
    """
    Создает рассадку студентов в аудитории с учетом ручных назначений
    """
    if manual_assignments is None:
        manual_assignments = {}

    assignments = {}
    used_students = set()

    # 1. Применяем ручные назначения
    for seat, student in manual_assignments.items():
        row, seat_num = seat
        # Проверяем, что место существует в аудитории
        if row <= len(row_config):
            # Рассчитываем общее количество мест в ряду
            seats_in_row = sum(2 for item in row_config[row - 1] if item == "desk")
            if seat_num <= seats_in_row:
                assignments[seat] = student
                used_students.add(student)
            else:
                st.error(f"CONFIG ERROR: Seat {seat} does not exist in the auditorium!")
        else:
            st.error(f"CONFIG ERROR: Row {row} does not exist in the auditorium!")

    # 2. Фильтруем студентов, которые еще не назначены
    remaining_students = [s for s in students if s not in used_students]
    student_index = 0
    total_rows = len(row_config)

    # 3. Автоматическая рассадка оставшихся студентов
    for row in range(total_rows):
        real_row_number = row + 1
        # Количество мест в ряду = количество парт * 2
        seats_in_row = sum(2 for item in row_config[row] if item == "desk")

        # Определяем стартовую позицию для шахматного порядка
        start_seat = 1

        for seat in range(start_seat, seats_in_row + 1, 2):
            seat_key = (real_row_number, seat)

            # Пропускаем места с ручными назначениями
            if seat_key in manual_assignments:
                continue

            if student_index < len(remaining_students):
                assignments[seat_key] = remaining_students[student_index]
                student_index += 1

    return assignments, student_index + len(manual_assignments)


def draw_classroom(assignments, row_config, auditorium_name, manual_assignments):
    """Отрисовывает схему аудитории с партами и пропусками"""
    selected_seat = st.session_state.get("selected_seat", None)
    total_rows = len(row_config)

    # Отрисовываем ряды ОТ ДАЛЬНЕГО К БЛИЖНЕМУ (сверху вниз)
    for display_row_index in range(total_rows - 1, -1, -1):
        real_row_number = display_row_index + 1
        row_items = row_config[display_row_index]

        # Рассчитываем общее количество колонок для ряда
        total_columns = 0
        for item in row_items:
            if item == "desk":
                total_columns += 2  # две колонки на парту
            elif item == "gap":
                total_columns += 1  # одна колонка на пропуск

        # Создаем контейнер для ряда (0.8 - для номера ряда, остальное - для парт и пропусков)
        cols = st.columns([0.8] + [1] * total_columns)

        # Подписываем ряд
        cols[0].markdown(f"**Ряд {real_row_number}**")

        # Начинаем с первой колонки после номера ряда
        col_index = 1
        seat_counter = 1

        # Отрисовываем элементы ряда
        for item in row_items:
            if item == "desk":
                # Отрисовываем парту (два места)
                desk_col1 = cols[col_index]
                desk_col2 = cols[col_index + 1]

                # Место 1 (левое)
                seat_key1 = (real_row_number, seat_counter)
                if seat_key1 in assignments:
                    student_name1 = assignments[seat_key1]
                    is_selected1 = (selected_seat == seat_key1)
                    button_type1 = "primary" if is_selected1 else "secondary"

                    if desk_col1.button(
                            f"{seat_counter}",
                            key=f"{auditorium_name}_seat_{real_row_number}_{seat_counter}",
                            type=button_type1,
                            help=f"Row: {real_row_number}, Seat: {seat_counter}\nStudent: {student_name1}"
                    ):
                        st.session_state.selected_seat = seat_key1
                        st.session_state.selected_student = student_name1
                        st.session_state.selected_auditorium = auditorium_name
                else:
                    desk_col1.button(
                        f"{seat_counter}",
                        disabled=True,
                        help=f"Row: {real_row_number}, Seat: {seat_counter}\n(free)"
                    )

                # Место 2 (правое)
                seat_key2 = (real_row_number, seat_counter + 1)
                if seat_key2 in assignments:
                    student_name2 = assignments[seat_key2]
                    is_selected2 = (selected_seat == seat_key2)
                    button_type2 = "primary" if is_selected2 else "secondary"

                    if desk_col2.button(
                            f"{seat_counter + 1}",
                            key=f"{auditorium_name}_seat_{real_row_number}_{seat_counter + 1}",
                            type=button_type2,
                            help=f"Row: {real_row_number}, Seat: {seat_counter + 1}\nStudent: {student_name2}"
                    ):
                        st.session_state.selected_seat = seat_key2
                        st.session_state.selected_student = student_name2
                        st.session_state.selected_auditorium = auditorium_name
                else:
                    desk_col2.button(
                        f"{seat_counter + 1}",
                        disabled=True,
                        help=f"Row: {real_row_number}, Seat: {seat_counter + 1}\n(free)"
                    )

                # Переходим к следующим колонкам и местам
                col_index += 2
                seat_counter += 2

            elif item == "gap":
                # Отображаем пропуск (пустая колонка)
                gap_col = cols[col_index]
                gap_col.markdown("<div style='width:100%; height:100%;'></div>", unsafe_allow_html=True)
                col_index += 1


# =============================================
# ИНТЕРФЕЙС ПРИЛОЖЕНИЯ
# =============================================

st.set_page_config(layout="wide", page_title="Differential Equations seating")
st.title("Seating in the exam on differential equations")

# Инициализация состояния
if "selected_auditorium" not in st.session_state:
    st.session_state.selected_auditorium = "R501"

# Выбор аудитории
auditorium_choice = st.radio(
    "Choose auditorium",
    options=list(AUDITORIUMS.keys()),
    format_func=lambda x: AUDITORIUMS[x]["name"],
    horizontal=True
)

# Получаем данные выбранной аудитории
auditorium = AUDITORIUMS[auditorium_choice]
row_config = auditorium["row_config"]
students = auditorium["students"]
name = auditorium["name"]
manual_assignments = auditorium.get("manual_assignments", {})
total_rows = len(row_config)

# Рассчитываем рассадку с учетом ручных назначений
assignments, placed_count = create_seating_chart(students, row_config, manual_assignments)

# Отображаем информацию о рассадке
total_seats = sum(sum(2 for item in row if item == "desk") for row in row_config)

if len(students) > placed_count:
    st.error(f"⚠️ {len(students) - placed_count} students did not fit in the auditorium!")

# Рисуем аудиторию
st.subheader(f"Auditorium: {name}")
draw_classroom(assignments, row_config, name, manual_assignments)

# Отображение информации о выбранном студенте
selected_seat = st.session_state.get("selected_seat", None)
selected_aud = st.session_state.get("selected_auditorium", None)



# Таблица с рассадкой
st.subheader("Student seating table")
if assignments:
    table_data = []
    for (row, seat), student in assignments.items():
        table_data.append({
            "Name": student,
            "Row": row,
            "Seat": seat,
            "Place": f"Row {row}, Seat {seat}"
        })

    df = pd.DataFrame(table_data)
    st.dataframe(
        df[["Name", "Place"]],
        hide_index=True,
        use_container_width=True
    )
else:
    st.warning("No data to display")

# Стили для разделения аудиторий
st.markdown("""
<style>
    div[data-testid="stRadio"] > label {
        font-size: 20px !important;
        font-weight: bold !important;
    }
    .stButton button {
        min-width: 40px !important;
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
        border-radius: 0.2rem;
        margin: 2px;
    }
    /* Стиль для парты */
    .desk-group {
        display: flex;
        border: 2px solid #555;
        border-radius: 5px;
        background-color: #f9f9f9;
        margin: 0 2px;
    }
    /* Стиль для пропуска */
    .gap-space {
        background-color: transparent;
        width: 20px;
    }
</style>
""", unsafe_allow_html=True)