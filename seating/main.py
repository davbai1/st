import streamlit as st
import pandas as pd
import plotly.express as px

# =============================================
# УТИЛИТА ДЛЯ ПАРСИНГА СПИСКА СТУДЕНТОВ ИЗ MULTILINE-СТРОКИ
# =============================================
def parse_students(raw: str) -> list[str]:
    """
    Преобразует многострочную строку,
    где каждое имя — на отдельной строке,
    в список имён без дополнительных кавычек.
    """
    return [line.strip() for line in raw.strip().splitlines() if line.strip()]

# =============================================
# НАСТРОЙКИ ЦВЕТОВ
# =============================================
OCCUPIED_COLOR = "#FF0000"   # цвет для занятых мест
EMPTY_COLOR    = "#808080"   # цвет для свободных мест

# =============================================
# КОНФИГУРАЦИЯ АУДИТОРИЙ
# =============================================
AUDITORIUM_101 = {
    "name": "Auditorium R503",
    "row_config": [
        ["desk","desk","gap","desk","desk","desk","desk","gap","desk","desk"],
        ["desk","desk","gap","desk","desk","desk","desk","gap","desk","desk"],
        ["desk","desk","gap","desk","desk","desk","desk","gap","desk","desk"],
        ["desk","desk","gap","desk","desk","desk","desk","gap","desk","desk"],
        ["desk","desk","gap","desk","desk","desk","desk","gap","desk","desk"],
        ["desk","desk","gap","desk","desk","desk","desk","gap","desk","desk"],
        ["desk","desk","gap","desk","desk","desk","desk","gap","desk","desk"],
    ],
    # Ряд 4 будет существовать, но оставаться пустым
    "skip_rows": [4],
    # Ещё не нужно ставить кавычки вокруг каждого имени
    "students": parse_students("""
Иванов Иван Иванович
Петров Петр Петрович
Сидорова Анна Михайловна
Кузнецов Дмитрий Сергеевич
Смирнова Екатерина Викторовна
Васильев Андрей Николаевич
Попова Ольга Дмитриевна
Новиков Александр Игоревич
Федорова Мария Александровна
Морозов Артем Олегович
Волкова Юлия Сергеевна
Алексеев Павел Денисович
Лебедева Анастасия Романовна
Козлов Игорь Вадимович
Егорова Дарья Евгеньевна
"""),
    "manual_assignments": {
        (1, 3): "Иванов Иван Иванович",
        (2, 1): "Сидорова Анна Михайловна"
    }
}

AUDITORIUM_201 = {
    "name": "Auditorium R505",
    "row_config": [
        ["gap","gap","desk","desk","desk","gap"],
        ["desk","desk","gap","gap","desk","desk"],
        ["desk","desk","gap","gap","desk","desk"],
        ["desk","desk","gap","gap","desk","desk"],
        ["desk","desk","gap","gap","desk","desk"],
        ["desk","desk","gap","gap","desk","desk"],
        ["desk","desk","gap","gap","desk","desk"],
    ],
    # Ряды 2 и 5 будут существовать, но оставаться пустыми
    "skip_rows": [2, 5],
    "students": parse_students("""
Тарасов Никита Владимирович
Андреева Вероника Станиславовна
Борисов Максим Юрьевич
Григорьева Елена Олеговна
Дмитриев Константин Александрович
Жукова Виктория Сергеевна
Захаров Артемий Игоревич
Ильина Марина Денисовна
Крылов Станислав Валерьевич
Ларина Ольга Павловна
Миронов Денис Андреевич
Николаева Анастасия Игоревна
Осипов Владислав Артемович
Павлова Кристина Романовна
"""),
    "manual_assignments": {
        (1, 1): "Тарасов Никита Владимирович",
        (3, 1): "Борисов Максим Юрьевич"
    }
}

# Ключи словаря должны совпадать с тем, что показываем в st.radio
AUDITORIUMS = {
    "R503": AUDITORIUM_101,
    "R505": AUDITORIUM_201
}

# =============================================
# ФУНКЦИЯ РАССАДКИ С УЧЁТОМ skip_rows
# =============================================
def create_seating_chart(students, row_config, manual_assignments=None, skip_rows=None):
    if manual_assignments is None:
        manual_assignments = {}
    if skip_rows is None:
        skip_rows = []
    assignments = {}
    used = set()

    # 1) Ручные назначения (пропускаем skip_rows)
    for (r, s), name in manual_assignments.items():
        if r in skip_rows:
            continue
        if 1 <= r <= len(row_config):
            max_seats = sum(2 for c in row_config[r-1] if c == "desk")
            if 1 <= s <= max_seats:
                assignments[(r, s)] = name
                used.add(name)
            else:
                st.error(f"CONFIG ERROR: место {(r, s)} отсутствует в ряду {r}!")
        else:
            st.error(f"CONFIG ERROR: ряд {r} отсутствует!")

    # 2) Автоматическая рассадка по оставшимся рядам
    remaining = [x for x in students if x not in used]
    idx = 0
    for r_idx, cfg in enumerate(row_config, start=1):
        if r_idx in skip_rows:
            continue
        seats = sum(2 for c in cfg if c == "desk")
        for seat in range(1, seats+1, 2):
            key = (r_idx, seat)
            if key in assignments:
                continue
            if idx < len(remaining):
                assignments[key] = remaining[idx]
                idx += 1

    return assignments

# =============================================
# UI STREAMLIT
# =============================================
st.set_page_config(layout="wide", page_title="Seating Chart")
st.title("Seating in the exam on differential equations")

choice = st.radio(
    "Choose auditorium",
    options=list(AUDITORIUMS.keys()),
    format_func=lambda k: AUDITORIUMS[k]["name"],
    horizontal=True
)

aud = AUDITORIUMS[choice]
row_config = aud["row_config"]
skip_rows  = aud.get("skip_rows", [])
students   = aud["students"]
manual     = aud.get("manual_assignments", {})

assignments = create_seating_chart(
    students,
    row_config,
    manual_assignments=manual,
    skip_rows=skip_rows
)

# Проверка переполнения (игнорируем skip_rows)
total_seats = sum(
    sum(2 for c in row if c == "desk")
    for idx, row in enumerate(row_config, start=1)
    if idx not in skip_rows
)
if len(students) > total_seats:
    st.error(f"⚠️ {len(students) - total_seats} студентов не уместились!")

st.subheader(aud["name"])

# Составляем DataFrame — рисуем все ряды, skip_rows останутся пустыми
rows = []
for r_idx, cfg in enumerate(row_config, start=1):
    col = 1
    seat = 1
    for item in cfg:
        if item == "desk":
            for _ in range(2):
                student   = assignments.get((r_idx, seat), "")
                help_text = f"{student} — seat {seat}" if student else ""
                rows.append({
                    "row": r_idx,
                    "col": col,
                    "help": help_text,
                    "occupied": bool(student)
                })
                seat += 1
                col  += 1
        else:
            col += 1

df = pd.DataFrame(rows)
df["marker_color"] = df["occupied"].map({
    True: OCCUPIED_COLOR,
    False: EMPTY_COLOR
})

# Рендер с Plotly и подписью снизу
fig = px.scatter(
    df,
    x="col",
    y="row",
    hover_data=["help"],
    labels={"col": "", "row": "Row"},
    height=len(row_config)*50,
)
fig.update_traces(
    marker=dict(size=20, color=df["marker_color"]),
    showlegend=False,
    hovertemplate="%{customdata[0]}<extra></extra>"
)
fig.update_yaxes(showgrid=False, tickmode="array",
                 tickvals=list(range(1, len(row_config)+1)),
                 autorange=True)
fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
fig.update_layout(
    margin=dict(l=20, r=20, t=20, b=80),  # отступ снизу для подписи
    dragmode=False,
    annotations=[{
        "text": "whiteboard",
        "x": 0.5, "xref": "paper",
        "y": -0.2, "yref": "paper",
        "showarrow": False,
        "font": {"size": 12}
    }]
)
st.plotly_chart(fig, use_container_width=True)

# Таблица рассадки
st.subheader("Student seating table")
table = [
    {"Name": nm, "Place": f"Row {r}, Seat {s}"}
    for (r, s), nm in assignments.items()
]
st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)
